# Exploration: fix-padron-moodle-por-tenant

> Phase: SDD explore · Artifact store: hybrid (engram `sdd/fix-padron-moodle-por-tenant/explore` + this file)
> Source: audit findings R-03 (CRITICAL), Q-01 (HIGH) from `docs/AUDITORIA-FALLAS.md`. Domain: Tenant / multi-tenancy → **CRITICAL governance**.

## Scope (proposed)

In: per-tenant Moodle credential model (Tenant + migration + AES-256) + worker iterating active tenants + padron router using tenant config instead of global. Out: admin UI to load credentials (Q-05, separate change).

## Current State (evidence)

- **R-03** (`backend/app/workers/main.py:30`): `await worker.run_once(tenants=[], sync_configs=[])` — hardcoded empty lists, never populated. Comment defers to "C-06 Tenant.moodle_url" which was never added. Nocturnal sync is a structural no-op.
- **Q-01** (`backend/app/core/config.py:33-34`): `moodle_url`/`moodle_token` are global `Settings` fields. `Tenant` model (`backend/app/models/tenant.py`) has NO Moodle fields — confirmed fields: `id, nombre, slug, activo, configuracion (JSONB), requiere_aprobacion_comunicaciones, created_at, updated_at`. Router (`padron.py:214,231`) builds `MoodleWSClient` from `Settings()` → all tenants share one Moodle → violates KB multi-tenant isolation.
- **Worker design is already correct**: `padron_sync_worker.py` iterates tenants, `getattr(tenant, "moodle_url", None)` → skips if None, catches `MoodleWSError` per tenant, continues. It just never receives real tenants; `run_once(db_session)` signature has the param but the caller never passes it.
- **No `TenantRepository`**: only precedent is raw `select(Tenant)` in `comunicacion_service.py:76`.

## KB grounding (confirmed by orchestrator)
Multi-tenant total isolation (`04_modelo_de_datos.md:9`) + "el LMS institucional —Moodle—" (`02_descripcion_general.md:9,11`) → config MUST be per-tenant. Global config contradicts the domain model. KB is agnostic about WHERE credentials live → design decision.

## Candidate Approaches (credential model)

| Approach | Pros | Cons |
|---|---|---|
| **A (rec)**: `moodle_url`/`moodle_token` nullable TEXT columns on `tenants`, AES-256 via `encrypt_pii` | matches PII column pattern (migration 006); simplest query; worker `getattr` already expects these names | `tenants` grows per integration |
| B: separate `configuracion_tenant` 1:1 entity | keeps `tenants` lean; extensible | extra join; new model+repo+migration; no precedent |
| C: reuse existing `configuracion` JSONB | zero migration | AES-256 base64 in JSONB breaks type safety + queryability; bad pattern |

**Recommendation: Approach A** — two nullable encrypted TEXT columns + one migration.

## ⚠️ Key gap surfaced — OQ-C09-01 (course_id mapping)
Even after R-03 + Q-01, the nocturnal loop STILL cannot call Moodle: there is no persisted mapping `Moodle course_id → materia × cohorte`. The on-demand endpoint takes it as a request param; the loop has nowhere to read it from. This was an open question from archived C-09, never closed. **Decision needed**: include a `moodle_course_id` column on `Materia` (full end-to-end sync) OR defer (loop populates the tenant list correctly but still no-ops the actual Moodle calls).

## Two deliverable slices (~200-250 LOC, one PR fine)
1. **Slice 1 (Q-01)**: add `moodle_url`/`moodle_token` to `Tenant` + migration + read from tenant in `padron.py` (on-demand sync). Independently deployable.
2. **Slice 2 (R-03 partial)**: populate `tenants` in `_padron_sync_loop` via DB query. Iterates real tenants; `sync_configs` stays empty until course_id mapping is resolved.

## Affected Files & Blast Radius
- `backend/app/models/tenant.py` — add `moodle_url`, `moodle_token` (Text, nullable)
- `backend/alembic/versions/017_tenant_moodle_config.py` (NEW) — add nullable columns on `tenants`
- `backend/app/repositories/tenant_repository.py` (NEW) — `list_active_with_moodle(db)` (raw select; Tenant has no `tenant_id`)
- `backend/app/workers/main.py` — replace `tenants=[]` with DB query via `AsyncSessionLocal`; pass `db_session`
- `backend/app/api/v1/routers/padron.py` — use `decrypt_pii(tenant.moodle_token)` instead of `Settings()`
- `backend/app/core/config.py` — keep global fields as deprecated fallback (`extra='forbid'` → removing breaks existing `.env`)
- tests: `test_moodle_sync_endpoint.py` (seed tenant fixture), `test_tenant_repository.py` (NEW)

## Test Strategy
Real DB per test; Moodle WS mocked via `unittest.mock.patch` (external HTTP, allowed). Seed multiple tenants with/without `moodle_url` to test worker iteration + skip. Existing `test_padron_sync_worker.py` (mocked `_FakeTenant`), `test_moodle_ws.py`, `test_moodle_sync_endpoint.py` pass today. NOTE: verify whether `test_padron_repository.py`/`test_padron_service.py` (seen failing in the full-suite baseline) are in scope or pre-existing-broken before relying on them.

## Risks & Open Questions (for propose/design)
1. **course_id mapping (OQ-C09-01)** — loop fix is INCOMPLETE without it. Include `moodle_course_id` on `Materia` or defer?
2. **Settings backward compat** — `extra='forbid'`; keep global fields as deprecated optional fallback.
3. **Migration safety** — nullable columns on `tenants`, safe.
4. **Initial credential load** — admin endpoint is Q-05 (out of scope); how are credentials seeded for testing? (fixtures write encrypted values directly).
5. **Governance CRITICAL** — Tenant + multi-tenancy; apply requires human approval.

## Hard Rules
Moodle credentials = secrets → AES-256 mandatory; multi-tenancy row-level; one migration per schema change; tests with real DB (Moodle client mocked); ≤500 LOC.

## Next
`sdd-propose`.
