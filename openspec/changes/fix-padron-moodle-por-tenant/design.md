# Design: Per-Tenant Moodle Configuration for Padron Sync

> Phase: SDD design · Artifact store: hybrid (engram `sdd/fix-padron-moodle-por-tenant/design` + this file)
> Domain: Tenant / multi-tenancy → **CRITICAL governance**. Reads: proposal + exploration.
> All names, migration numbers and signatures below are CONFIRMED against the real code.

## 1. Architecture approach

Minimal, additive, layered change that respects the unidirectional flow `Routers → Services/Workers → Repositories → Models`. No new entity, no new service: two encrypted columns on the existing `Tenant` model, one Alembic migration (schema-only), one thin read-only repository, and decryption pushed to the **call site** where `MoodleWSClient` is constructed.

Core principle: **the database stores ciphertext; the application decrypts at the point of use.** This mirrors the existing PII pattern (migration `006_usuario_pii_asignacion`, `core/encryption.py`). The migration NEVER encrypts/decrypts and carries NO data migration — it only adds two nullable `Text` columns.

```
                         writes ciphertext            reads ciphertext
  (out of scope: admin UI Q-05) ─────► Tenant.moodle_url / moodle_token (Text, nullable)
                                              │
              ┌───────────────────────────────┴───────────────────────────────┐
              │ on-demand path (router)                  nightly path (worker)  │
              ▼                                            ▼                     │
  padron.py moodle_sync()                      workers/main.py _padron_sync_loop()
   - load session Tenant (select)               - AsyncSessionLocal()
   - decrypt_pii(tenant.moodle_token)           - TenantRepository.list_active_with_moodle(db)
   - MoodleWSClient(url, token)                  - run_once(tenants=..., sync_configs=[], db_session=db)
                                                     └─ _sync_one decrypts before MoodleWSClient(...)
```

## 2. Data model

Two columns added to `Tenant` (`backend/app/models/tenant.py`, `__tablename__ = "tenants"`). `Tenant` does NOT inherit `BaseModelMixin` (no `tenant_id`, no `deleted_at` — it is the global root). The columns follow the confirmed `Mapped[...] / mapped_column` style of the file:

```python
moodle_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
moodle_token: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
```

- Type `Text` (not `String(n)`): ciphertext length is variable (base64 of nonce+tag+ciphertext) — matches the PII columns added to `usuarios` in migration 006 (`sa.Text(), nullable=True`).
- Both nullable: a tenant without Moodle integration leaves them `NULL`. NULL is the explicit "not configured" signal across both code paths.
- `moodle_url` stores ciphertext too (it is decrypted alongside the token). Storing the URL encrypted is consistent and avoids leaking institution endpoints; `MoodleWSClient` receives the decrypted URL.
- Requires `from sqlalchemy import Text` added to the existing import line.

### Encryption boundary (decision)

Encryption/decryption lives in the **application layer only**, never in the migration and never in the ORM model:

- **Write** (`encrypt_pii(plain)`): performed by whatever writes credentials. The writer (admin endpoint) is **Q-05, out of scope**. For this change, encrypted values are written only by test fixtures and any manual seed. Documented gotcha: nothing in-scope writes credentials at runtime.
- **Read** (`decrypt_pii(cipher)`): performed at the **call site that builds `MoodleWSClient`**, in BOTH paths. The ORM attribute always holds ciphertext; decryption is explicit and local, so plaintext never lives on the model or crosses repository boundaries.

`core/encryption.py` confirmed signatures: `encrypt_pii(plain_text: str) -> str`, `decrypt_pii(cipher_text: str) -> str`, raises `EncryptionError` on tamper/corruption.

### NULL / not-configured handling

`MoodleWSClient.__init__(moodle_url: str | None, token: str)` already raises `MoodleNotConfiguredError` when `moodle_url` is falsy (confirmed `moodle_ws.py:63-65`). So:

- **Router path**: if the session tenant has `moodle_url IS NULL` → do not attempt decryption; return HTTP 422 `MOODLE_NOT_CONFIGURED` (same contract as today's global-Settings guard).
- **Worker path**: `list_active_with_moodle` already filters `moodle_url IS NOT NULL`, so the worker only ever sees configured tenants. The worker's existing `if not moodle_url: continue` skip remains as defense-in-depth.

## 3. Migration

**File: `backend/alembic/versions/017_tenant_moodle_config.py` (NEW).**

CONFIRMED revision chain (traced full `down_revision` graph, not assumed):
- Single head today is `016_c20_mensaje_perfil` (016 → 015 → 014 → 013 → 012 → 011 → 010 → 009 → 008; 008 merges branches `007_padron` + `007_slot_encuentro_instancia_guardia`, both → 006 → 005 → 004 → 002 → `3a51a71a68ef` → `001_tenant`).
- Therefore:

```python
revision: str = "017_tenant_moodle_config"
down_revision: Union[str, Sequence[str], None] = "016_c20_mensaje_perfil"
```

Schema-only, no data migration, no encryption logic:

```python
def upgrade() -> None:
    op.add_column("tenants", sa.Column("moodle_url", sa.Text(), nullable=True))
    op.add_column("tenants", sa.Column("moodle_token", sa.Text(), nullable=True))

def downgrade() -> None:
    op.drop_column("tenants", "moodle_token")
    op.drop_column("tenants", "moodle_url")
```

Safe by construction: nullable columns on an existing table, no backfill, clean `downgrade -1`.

## 4. TenantRepository (NEW)

**File: `backend/app/repositories/tenant_repository.py` (NEW).**

Cannot extend `BaseRepository`: that base requires a non-null `tenant_id` (fail-closed `ValueError`), but `Tenant` IS the tenant root and has no `tenant_id` column. Precedent for raw `select(Tenant)` is `comunicacion_service.py:75`. So this is a thin, explicit repository with one read method:

```python
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tenant import Tenant

class TenantRepository:
    """Read-only access to the global Tenant root (no tenant_id scope: Tenant IS the tenant)."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    async def list_active_with_moodle(self) -> Sequence[Tenant]:
        """Active tenants that have Moodle configured (ciphertext columns non-null)."""
        result = await self.db_session.execute(
            select(Tenant).where(
                Tenant.activo.is_(True),
                Tenant.moodle_url.is_not(None),
            )
        )
        return result.scalars().all()
```

- Constructor takes only `db_session` (no `tenant_id`) — this is the deliberate exception, documented in the docstring because it would otherwise look like a multi-tenancy violation in code review.
- Returns raw `Tenant` ORM objects (ciphertext). Decryption is NOT done here — kept at the call site so the repository has no crypto dependency and plaintext never leaves the worker/router scope.
- `WHERE activo = true AND moodle_url IS NOT NULL`. We filter on `moodle_url` (the presence signal); `moodle_token` may be checked at the call site if needed, but a configured tenant is expected to have both.

> Note: skeleton uses a zero-arg `list_active_with_moodle(self)`; the worker calls `repo.list_active_with_moodle()`. If a `db`-passed signature is preferred for symmetry with other repos, it can be `list_active_with_moodle(self)` with `db` injected via constructor — constructor injection chosen for consistency with `ComunicacionRepository(db_session, tenant_id)`.

## 5. Worker wiring

**File: `backend/app/workers/main.py` — modify `_padron_sync_loop`.**

CONFIRMED `run_once` signature (`padron_sync_worker.py:35`):
```python
async def run_once(self, *, tenants: list[Any], sync_configs: list[Any], db_session: Any = None) -> None
```
All keyword-only. The loop must pass `tenants`, `sync_configs`, and `db_session`.

CONFIRMED session source: `from app.core.database import AsyncSessionLocal` (already used by the comunicacion loop, which guards `AsyncSessionLocal is None`). Replace the hardcoded `run_once(tenants=[], sync_configs=[])`:

```python
from app.core.database import AsyncSessionLocal
from app.repositories.tenant_repository import TenantRepository

async def _padron_sync_loop() -> None:
    worker = PadronSyncWorker()
    while True:
        try:
            if AsyncSessionLocal is None:
                logger.warning("padron_sync_loop_db_not_ready")
            else:
                db_session = AsyncSessionLocal()
                try:
                    tenants = await TenantRepository(db_session).list_active_with_moodle()
                    # sync_configs stays [] until course_id mapping exists (OQ-C09-01, OUT of scope).
                    await worker.run_once(
                        tenants=tenants, sync_configs=[], db_session=db_session,
                    )
                finally:
                    await db_session.close()
        except Exception:
            logger.exception("padron_sync_loop_unhandled_error")
        await asyncio.sleep(_PADRON_SYNC_INTERVAL_SECONDS)
```

### Worker decryption (decision)

`run_once` → `_sync_one` currently passes `moodle_token` raw to `MoodleWSClient`. Since the column now holds ciphertext, `_sync_one` must `decrypt_pii(moodle_url)` and `decrypt_pii(moodle_token)` immediately before constructing the client. Minimal edit in `padron_sync_worker.py._sync_one`:

```python
from app.core.encryption import decrypt_pii
...
client = MoodleWSClient(decrypt_pii(moodle_url), decrypt_pii(moodle_token))
```

`moodle_token` falsy guard stays (`decrypt_pii("")` would raise `EncryptionError`; the `or ""` default plus an explicit empty check avoids decrypting empty strings). Because `sync_configs=[]` in this change, `_sync_one` is never actually invoked at runtime yet — but the decryption wiring is added so the worker is correct the moment course_id mapping lands. This keeps the worker honest without changing its no-op-by-design behavior for this change.

## 6. Router path

**File: `backend/app/api/v1/routers/padron.py` — modify `moodle_sync` (~:211-231).**

Today it reads global `Settings().moodle_url/moodle_token`. New flow uses the **session tenant** (`current_user.tenant_id`, identity from JWT — Hard Rule 8):

1. Load the tenant: raw `select(Tenant).where(Tenant.id == current_user.tenant_id)` (same pattern as `comunicacion_service._get_tenant`). May reuse `TenantRepository` with a `get_by_id` helper, or inline select — inline select keeps the repository read-surface minimal; a `get_by_id` on the repo is the cleaner option and is preferred.
2. If `tenant.moodle_url is None` → HTTP 422 `MOODLE_NOT_CONFIGURED` (preserves existing contract).
3. `client = MoodleWSClient(decrypt_pii(tenant.moodle_url), decrypt_pii(tenant.moodle_token or ""))` — but token empty/None must be guarded to avoid `EncryptionError`. If `moodle_token` is None → treat as not configured (422), since a URL without a token cannot authenticate.
4. Keep existing `except MoodleNotConfiguredError → 422` and `except MoodleWSError → 502` handlers unchanged.

Global `Settings()` import for moodle is removed from this handler.

## 7. Settings fallback (deprecated)

**File: `backend/app/core/config.py:33-34` — keep, annotate.**

`extra="forbid"` (confirmed `config.py` model config) means removing `moodle_url`/`moodle_token` from `Settings` would make any existing `.env` carrying `MOODLE_URL`/`MOODLE_TOKEN` fail at startup. Decision: **keep both fields**, mark deprecated via the `Field(description=...)` and a code comment. They are no longer read by the router or worker after this change; they remain only so legacy `.env` files load. Removal is a future cleanup change.

```python
moodle_url: str | None = Field(default=None, description="DEPRECATED: use Tenant.moodle_url. Kept for .env back-compat (extra='forbid').")
moodle_token: str | None = Field(default=None, description="DEPRECATED: use Tenant.moodle_token. Kept for .env back-compat.")
```

No behavior change to `Settings`; only documentation. `extra='forbid'` stays intact.

## 8. Test design

Hard Rule 4: real DB, no DB mocks. External HTTP (Moodle WS) is mocked.

### Fixtures — writing encrypted credentials

Tenants are seeded directly into the real test DB. Credentials are written as **ciphertext** using the real `encrypt_pii`, exactly as production expects:

```python
from app.core.encryption import encrypt_pii
tenant_with = Tenant(
    nombre="Inst A", slug="inst-a", activo=True,
    moodle_url=encrypt_pii("https://moodle-a.example"),
    moodle_token=encrypt_pii("token-a"),
)
tenant_without = Tenant(nombre="Inst B", slug="inst-b", activo=True)  # NULL columns
tenant_inactive = Tenant(nombre="Inst C", slug="inst-c", activo=False,
    moodle_url=encrypt_pii("https://moodle-c.example"), moodle_token=encrypt_pii("token-c"))
```

Two configured tenants are seeded to assert **isolation** (the repository returns only the active-with-moodle set, never another tenant's row).

### New test: `backend/tests/test_tenant_repository.py`
- `list_active_with_moodle` returns the active+configured tenant, excludes the NULL-moodle tenant, excludes the inactive tenant.
- With two configured active tenants, both are returned and each carries its OWN ciphertext (decrypt each → distinct plaintext) — proves no cross-tenant credential bleed.
- Stored value is ciphertext, not plaintext (`tenant.moodle_token != "token-a"`, and `decrypt_pii(tenant.moodle_token) == "token-a"`).

### Existing in-domain tests
- `test_padron_sync_worker.py`: uses `_FakeTenant` with plain `moodle_url`/`moodle_token` attributes and patches `MoodleWSClient`. With worker decryption added, the fake's plaintext values would now be passed through `decrypt_pii` → these tests must either (a) seed `encrypt_pii(...)` values into `_FakeTenant`, or (b) patch `decrypt_pii` to identity. Preferred: update `_FakeTenant` usages to encrypt, keeping the test faithful to runtime. This is a required test update, flagged for `sdd-tasks`.
- `test_moodle_sync_endpoint.py`: add/seed a session tenant fixture with encrypted `moodle_url`/`moodle_token`; assert the client is built from the tenant (not global Settings). Mock `MoodleWSClient.get_padron_rows`. Add a case: tenant with NULL moodle → 422.

### Pre-existing-broken (NOT this change's domain)
`test_padron_repository.py` / `test_padron_service.py` are C-09 import-pipeline tests (CSV/XLSX), zero Moodle references — do NOT block this change's TDD (confirmed in proposal §Open Questions 2).

## 9. File-level change plan (LOC confirmed < 500 each)

| File | Type | Change | Approx LOC |
|------|------|--------|-----------|
| `backend/app/models/tenant.py` | Modify | +2 columns, +`Text` import | ~66 → ~70 |
| `backend/alembic/versions/017_tenant_moodle_config.py` | New | schema-only up/down | ~30 |
| `backend/app/repositories/tenant_repository.py` | New | `TenantRepository` + `list_active_with_moodle` (+ optional `get_by_id`) | ~35 |
| `backend/app/workers/main.py` | Modify | DB query + pass `db_session` | ~104 → ~120 |
| `backend/app/workers/padron_sync_worker.py` | Modify | `decrypt_pii` at client construction | ~109 → ~115 |
| `backend/app/api/v1/routers/padron.py` | Modify | session-tenant creds instead of `Settings()` | within file, +~10 |
| `backend/app/core/config.py` | Modify | deprecation comments only | no net LOC |
| `backend/tests/test_tenant_repository.py` | New | repo isolation tests | ~80 |
| `backend/tests/test_padron_sync_worker.py` | Modify | encrypt fake tenant creds | small |
| `backend/tests/test_moodle_sync_endpoint.py` | Modify | seed encrypted session tenant | small |

All backend files stay well under the 500 LOC hard limit.

## 10. ADR-style decisions

- **ADR-1: Encrypt at app layer, store ciphertext, decrypt at call site.** Rejected: encrypting inside the ORM model (`@validates`/hybrid) — would leak crypto into the model and make raw queries return plaintext inconsistently. Rejected: decrypting inside the repository — would spread plaintext beyond the single call site and couple the repo to `encryption.py`. Chosen approach keeps the model crypto-free and decryption explicit and local.
- **ADR-2: Two `Text` columns on `tenants`, not a 1:1 config entity nor JSONB.** Rationale: matches the existing PII column pattern (migration 006), simplest query, and the worker's `getattr(tenant, "moodle_url")` already expects these exact names. Rejected: separate `configuracion_tenant` entity (extra join, new repo/migration, no precedent); reusing `configuracion` JSONB (base64 ciphertext in JSONB breaks type safety/queryability).
- **ADR-3: `TenantRepository` does NOT extend `BaseRepository`.** Rationale: `BaseRepository` fail-closes on missing `tenant_id`, but `Tenant` is the tenant root and has none. Documented exception with a docstring so it does not read as a multi-tenancy violation.
- **ADR-4: Keep global `Settings.moodle_url/moodle_token` as deprecated fallback.** Rationale: `extra='forbid'` would break existing `.env` files if removed. Tenant config is authoritative; global fields kept only for back-compat, slated for a later cleanup change.
- **ADR-5: Worker wiring lands decryption even though `sync_configs=[]`.** Rationale: `_sync_one` is not invoked at runtime in this change (no course_id mapping), but adding the decrypt at the client-construction site makes the worker correct the instant the follow-up change supplies configs, with no second touch of this file.

## 11. Open design points

- **course_id mapping (OQ-C09-01) — OUT of scope, already tracked.** No persisted `Moodle course_id → materia × cohorte` mapping exists. `sync_configs` stays `[]`; the worker iterates real tenants but does NOT call Moodle yet. Tracked URGENT in engram (`open-decisions/moodle-course-id-mapping`). Follow-up change required for end-to-end nightly sync.
- **Initial credential seeding (Q-05) — OUT of scope.** No runtime writer of credentials in this change. Admin UI / endpoint to load encrypted credentials is a separate change. In-scope writes happen only via test fixtures (and manual seed).
- **Router tenant loader shape.** Inline `select(Tenant)` vs a `TenantRepository.get_by_id` helper — minor; `get_by_id` preferred for symmetry. Decided at `sdd-tasks`/apply, no architectural impact.

## 12. Governance

**CRITICAL** (Tenant + multi-tenancy). `sdd-apply` requires explicit human approval before writing code. Credentials = secrets → AES-256 mandatory (Hard Rule 12); identity from session JWT only (Hard Rule 8); one migration per schema change (Hard Rule 15).

## Next
`sdd-tasks` (after spec is ready).
