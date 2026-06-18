# Proposal: Per-Tenant Moodle Configuration for Padron Sync

> Phase: SDD propose · Artifact store: hybrid · Domain: Tenant / multi-tenancy → **CRITICAL governance**
> Source: audit findings R-03 (CRITICAL), Q-01 (HIGH). Scope decided by user: **narrow (option 1)**.

## Intent

Enable per-tenant Moodle credentials (correct multi-tenant isolation) and make the nightly worker iterate real active tenants instead of a hardcoded empty list.

## Scope

### In Scope
- **Q-01**: add nullable `moodle_url` / `moodle_token` (`Text`, AES-256 via `encrypt_pii`/`decrypt_pii`) to `Tenant` + Alembic migration `017_tenant_moodle_config.py` (nullable, no data migration). `padron.py` on-demand sync reads `decrypt_pii(tenant.moodle_token)` from the session tenant instead of global `Settings()`.
- **R-03 (partial)**: new `TenantRepository.list_active_with_moodle(db)` (raw `select(Tenant)`; Tenant has no `tenant_id`). `workers/main.py:30` replaces `tenants=[]` with this query and passes `db_session` to `run_once`.

### Out of Scope
- **course_id mapping (OQ-C09-01)** — **EXPLICIT LIMITATION**: no persisted `Moodle course_id → materia × cohorte` mapping exists. `sync_configs` stays empty; the worker iterates tenants but does NOT call Moodle yet. Tracked as **open + URGENT** in engram (`open-decisions/moodle-course-id-mapping`). **Follow-up change required.**
- Admin UI for credential entry (Q-05) — separate change.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `padron-sync`: Moodle credentials become per-tenant (session tenant), not global; nightly worker iterates real active tenants with Moodle configured.

## Approach

**Approach A** (per exploration): two nullable encrypted `Text` columns on `tenants` (matches PII pattern from migration 006) + one migration + `TenantRepository.list_active_with_moodle` + worker DB query. The padron worker already iterates, reads `getattr(tenant, "moodle_url", None)`, skips on None, and catches `MoodleWSError` per tenant — it only lacked real input.

## Open Questions Resolved (with evidence)

**1. Settings backward compatibility** — `config.py:15-19` sets `extra="forbid"`; `moodle_url`/`moodle_token` are global fields (`:33-34`). **Decision: KEEP them as a deprecated optional fallback (do NOT remove).** Removing them would force every existing `.env` carrying `MOODLE_URL`/`MOODLE_TOKEN` to fail at startup (`extra="forbid"` rejects unknown env keys). Tenant config is authoritative; global values are a documented deprecated fallback for single-tenant dev. Mark with a deprecation comment; plan removal in a later cleanup change.

**2. Test discrepancy** — VERIFIED. `test_padron_repository.py` and `test_padron_service.py` are **C-09 import-pipeline tests** (CSV/XLSX parsing, `Materia`/`Carrera`/`Cohorte`); zero references to Moodle, credentials, or `run_once` (grep count = 0 in both). They are **pre-existing-broken and OUT of this change's domain** — they do NOT block this change's TDD. The relevant in-domain tests are `test_padron_sync_worker.py` and `test_moodle_sync_endpoint.py`, which pass today. New test: `test_tenant_repository.py`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/tenant.py` | Modified | add `moodle_url`, `moodle_token` (Text, nullable, encrypted) |
| `backend/alembic/versions/017_tenant_moodle_config.py` | New | nullable columns on `tenants` |
| `backend/app/repositories/tenant_repository.py` | New | `list_active_with_moodle(db)` raw select |
| `backend/app/workers/main.py` | Modified | replace `tenants=[]` with DB query; pass `db_session` |
| `backend/app/api/v1/routers/padron.py` | Modified | use `decrypt_pii(tenant.moodle_token)` instead of `Settings()` |
| `backend/app/core/config.py` | Modified | comment global fields as deprecated fallback |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Worker iterates but no Moodle call (course_id gap) | High (known) | Documented out-of-scope; tenant list populated correctly; follow-up tracked |
| Plaintext credential leak | Low | AES-256 mandatory; decrypt only at call site |
| Migration breaks existing rows | Low | Columns nullable, no data migration |
| Removing global Settings breaks `.env` | Avoided | Keep as deprecated fallback |

## Hard Rules
Credentials = secrets → AES-256; multi-tenancy row-level; one migration per schema change; tests use real DB with Moodle WS mocked; ≤500 LOC per file.

## Governance
**CRITICAL** (Tenant + multi-tenancy). `sdd-apply` requires explicit human approval before writing code.

## KB Grounding
Total multi-tenant isolation + institutional Moodle ⟹ Moodle config MUST live per tenant; global config contradicts the domain model.

## Rollback Plan
Revert the migration (`alembic downgrade -1`, drops nullable columns) and revert worker/router/repo changes. Global `Settings` fallback remains, so on-demand sync continues working as before.

## Success Criteria
- [ ] `Tenant` has encrypted `moodle_url`/`moodle_token`; migration applies and downgrades cleanly.
- [ ] On-demand `padron.py` sync uses the session tenant's decrypted credentials.
- [ ] Worker iterates active tenants with Moodle configured (real query), skips those without.
- [ ] In-domain tests pass (`test_moodle_sync_endpoint.py`, `test_padron_sync_worker.py`, new `test_tenant_repository.py`).
- [ ] course_id limitation documented; follow-up tracked in engram.
