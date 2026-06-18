# Padron-Sync Specification

> Change: fix-padron-moodle-por-tenant · Domain: padron-sync · Governance: CRITICAL (Tenant / multi-tenancy)

## Purpose

Define behavior for per-tenant Moodle credential storage, on-demand padron sync using the session tenant's credentials, and nightly worker iteration over active tenants with Moodle configured.

---

## Requirements

### Requirement: Tenant Moodle Credential Storage

The `Tenant` model MUST expose two nullable encrypted fields — `moodle_url` (Text) and `moodle_token` (Text) — stored in the database exclusively as AES-256 ciphertext via `encrypt_pii`. Plaintext MUST NOT be persisted at any layer. A single Alembic migration (`017_tenant_moodle_config.py`) MUST add both nullable columns to the `tenants` table with no data migration.

#### Scenario: Store credentials for a tenant

- GIVEN a `Tenant` row exists with `activo=True`
- WHEN `moodle_url` and `moodle_token` are written via `encrypt_pii`
- THEN the database column values are AES-256 ciphertext, not plaintext
- AND `decrypt_pii(tenant.moodle_token)` returns the original token value

#### Scenario: Tenant without Moodle credentials

- GIVEN a `Tenant` row with `moodle_url=NULL` and `moodle_token=NULL`
- WHEN the row is read from the database
- THEN both fields are `None` without error
- AND no decryption is attempted

#### Scenario: Migration applies and rolls back cleanly

- GIVEN the database at migration `016`
- WHEN `alembic upgrade head` is run
- THEN columns `moodle_url` and `moodle_token` exist on `tenants` as nullable TEXT
- AND `alembic downgrade -1` removes them without data loss on other columns

---

### Requirement: Tenant Repository — Active-with-Moodle Query

`TenantRepository` MUST provide an async method `list_active_with_moodle(db)` that returns all `Tenant` rows where `activo=True` AND `moodle_url IS NOT NULL`. The query MUST NOT return tenants belonging to another tenant (Tenant has no `tenant_id`; the table IS the root; all rows are returned if active and configured).

#### Scenario: Multiple tenants, only some with Moodle configured

- GIVEN tenants T1 (`activo=True`, `moodle_url` set), T2 (`activo=True`, `moodle_url=NULL`), T3 (`activo=False`, `moodle_url` set)
- WHEN `list_active_with_moodle(db)` is called
- THEN only T1 is returned

#### Scenario: No tenants with Moodle configured

- GIVEN no tenant has `moodle_url` set
- WHEN `list_active_with_moodle(db)` is called
- THEN an empty list is returned without error

---

### Requirement: On-Demand Padron Sync — Per-Tenant Credentials

The padron router on-demand sync endpoint MUST source Moodle credentials exclusively from the **session tenant** (extracted from the verified JWT). It MUST NOT read from global `Settings()`. The `MoodleWSClient` MUST be instantiated with `decrypt_pii(tenant.moodle_token)` and `tenant.moodle_url`.

#### Scenario: On-demand sync with configured tenant

- GIVEN an authenticated request where the session tenant has `moodle_url` and `moodle_token` set
- WHEN the on-demand padron sync endpoint is called
- THEN `MoodleWSClient` is instantiated with the tenant's decrypted credentials
- AND the global `Settings().moodle_token` is never read

#### Scenario: On-demand sync — tenant has no Moodle credentials

- GIVEN an authenticated request where the session tenant has `moodle_url=NULL`
- WHEN the on-demand padron sync endpoint is called
- THEN the endpoint returns a controlled error (e.g., `503` or `422`) with a message indicating Moodle is not configured for this tenant
- AND no `MoodleWSClient` is instantiated

#### Scenario: Tenant isolation — tenant A cannot use tenant B credentials

- GIVEN tenant A and tenant B each with distinct Moodle credentials
- WHEN a request authenticated as tenant A triggers on-demand sync
- THEN the client is built from tenant A's credentials exclusively
- AND tenant B's credentials are never read or used

---

### Requirement: Nightly Worker — Iterates Active Tenants with Moodle

`workers/main.py` MUST replace the hardcoded `tenants=[]` with a live DB query using `TenantRepository.list_active_with_moodle(db)`. The worker MUST pass the resulting tenant list (and a `db_session`) to `run_once`. Tenants without Moodle configured MUST be silently skipped. A `MoodleWSError` for one tenant MUST NOT abort processing of subsequent tenants.

#### Scenario: Worker iterates tenants with Moodle configured

- GIVEN two active tenants with `moodle_url` set and one active tenant without
- WHEN the nightly worker executes `run_once`
- THEN `run_once` is called with a list containing only the two configured tenants
- AND the unconfigured tenant is not passed to `run_once`

#### Scenario: Moodle error in one tenant does not abort others

- GIVEN two tenants T1 and T2 both with Moodle configured, T1's Moodle raises `MoodleWSError`
- WHEN the worker processes the tenant list
- THEN T1's error is caught and logged
- AND T2 is processed without interruption

#### Scenario: No active tenants with Moodle configured

- GIVEN no tenant has `moodle_url` set
- WHEN the nightly worker executes
- THEN `run_once` is called with an empty tenant list (or skipped entirely)
- AND no exception is raised

---

### Requirement: Known Limitation — course_id Mapping Gap

With `sync_configs` empty (no persisted `Moodle course_id → materia × cohorte` mapping), the worker MUST iterate tenants correctly but MUST NOT call the Moodle sync API. The limitation MUST be documented in code (inline comment referencing OQ-C09-01) and tracked in engram (`open-decisions/moodle-course-id-mapping`). A follow-up change is required to resolve OQ-C09-01 before end-to-end nightly sync is operational.

#### Scenario: Worker runs with empty sync_configs

- GIVEN active tenants with Moodle configured but `sync_configs=[]`
- WHEN the nightly worker executes
- THEN the worker iterates tenants, finds no sync configs to process
- AND exits cleanly without calling Moodle APIs
- AND no error is raised

---

### Requirement: Global Settings — Deprecated Fallback

The global `moodle_url` / `moodle_token` fields in `Settings` (config.py) MUST be kept as a deprecated optional fallback. They MUST be annotated with a deprecation comment. They MUST NOT be removed in this change. Removing them would break startup for any `.env` carrying those keys under `extra="forbid"`.

#### Scenario: Global fields remain at startup

- GIVEN a `.env` file with `MOODLE_URL` and `MOODLE_TOKEN` set
- WHEN the application starts
- THEN startup does not raise a Pydantic validation error
- AND the global values are not used by any in-scope code path that has tenant credentials available

---

## Hard Rules

| Category | Rule |
|----------|------|
| Credentials | MUST be stored AES-256 (`encrypt_pii`). Plaintext in DB is a CRITICAL defect. |
| Multi-tenancy | Sync endpoint MUST source credentials from session JWT tenant ONLY. Cross-tenant credential read is a CRITICAL defect. |
| Migration | One Alembic migration per schema change. Columns nullable. No data migration. |
| Tests | Real DB (ephemeral test container). Moodle WS client mocked via `unittest.mock.patch`. No DB mocks. |
| File size | ≤500 LOC per backend file. |
| Governance | CRITICAL domain — `sdd-apply` requires explicit human approval before writing code. |
