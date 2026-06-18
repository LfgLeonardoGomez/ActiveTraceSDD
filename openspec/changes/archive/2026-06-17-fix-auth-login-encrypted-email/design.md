# Design: Fix login/forgot lookup against AES-encrypted email + readable impersonation audit

## Technical Approach

Targeted inline hotfix (proposal Approach A/C). The router currently queries the
non-deterministic AES-256-GCM `usuarios.email` ciphertext with plaintext, so it never
matches. We replace those raw queries with a lookup on the deterministic `email_hash`
column using the existing `hash_email_for_lookup(email)` (confirmed in
`backend/app/core/encryption.py:96`, already imported by `usuarios.py:21`). We do NOT
route through `AuthService`/`UsuarioRepository` — that architectural cleanup is deferred
to Q-02. Maps to spec capability `user-auth` (login, forgot, impersonation-audit).

## Architecture Decisions

| Decision | Choice | Alternatives rejected | Rationale |
|---|---|---|---|
| Lookup mechanism | Replace `WHERE Usuario.email == body.email` with `WHERE Usuario.email_hash == hash_email_for_lookup(body.email)` (login + forgot) | (a) Wire `AuthService.authenticate()`; (b) call `UsuarioRepository.get_by_email_hash()` | `email` is non-deterministic ciphertext — never matches. `get_by_email_hash` is tenant-scoped + uses `scalar_one_or_none` (crashes cross-tenant). AuthService needs a cross-tenant variant = larger blast radius for a CRITICAL hotfix. Inline `hash_email_for_lookup` is the minimal correct fix. |
| Cross-tenant duplicate result | `.scalars().first()` with stable `ORDER BY Usuario.created_at` | `scalar_one_or_none()` | Index `idx_usuarios_tenant_email_hash` is UNIQUE on `(tenant_id, email_hash)` (migration 006:110-116) — tenant-scoped, NOT global. Same email in two tenants = same hash = multiple rows. `scalar_one_or_none()` raises `MultipleResultsFound` (500). `.first()` + deterministic order authenticates a stable first match without crashing. |
| NULL `email_hash` (legacy) | No match → existing timing-safe dummy-hash 401 path | Add backfill migration | Login already runs `verify_password(password, DUMMY_HASH)` on miss (auth.py:138-144). NULL hash simply yields no row → normal 401, preserves anti-enumeration (R2). Backfill is idempotent/operational, broadens a CRITICAL hotfix → deferred. |
| Impersonation audit (R-07) | Wrap `target.email` with `decrypt_pii()` in try/except fallback before `record_audit` | Log raw `target.email`; decrypt at read time | Raw value is base64 ciphertext — unreadable audit. Pattern already established in `dependencies.py:125-128,151-154`. Try/except keeps legacy plaintext rows working. |
| Stay in router (rule #11) | Accept business logic in router as known debt | Refactor now | CRITICAL prod hotfix; refactor belongs to Q-02 which reorganizes this file anyway. Documented as conscious debt. |

## Data Flow

Login / forgot after the fix:

    POST /api/auth/login {email, password}
        │
        ├─ _check_rate_limit
        ├─ h = hash_email_for_lookup(email)            # HMAC-SHA256, deterministic
        ├─ SELECT Usuario WHERE email_hash == h
        │     AND deleted_at IS NULL ORDER BY created_at
        │     → .scalars().first()
        ├─ if None or password_hash None → verify(DUMMY_HASH) → 401   # timing-safe
        ├─ verify_password(password, user.password_hash) (Argon2id) → 401 on fail
        ├─ if is_2fa_enabled → PreAuthResponse
        └─ TokenService.issue_token_pair → access + refresh cookie

Impersonation (R-07):

    target = SELECT Usuario (tenant-scoped, unchanged)
        │
        ├─ plain = try decrypt_pii(target.email) except → target.email   # legacy
        └─ record_audit(detalle={"target_email": plain})

## File Changes

| File | Action | Description |
|---|---|---|
| `backend/app/api/v1/routers/auth.py` | Modify | login (130-136) + forgot (245-251): hash lookup, `ORDER BY created_at`, `.scalars().first()`. Import `hash_email_for_lookup`, `decrypt_pii` from `app.core.encryption`. impersonation (556): wrap with decrypt try/except. +~15 LOC → file at 586, already over rule #16 (Q-02 debt). |
| `backend/tests/test_auth.py` | Modify | `_create_test_user()` → `UsuarioRepository(db_session, tenant_id).create(...)` (no explicit tenant_id) so `email` is ciphertext + `email_hash` computed. Existing tests become true regression. |
| `backend/tests/test_auth_c07.py` | Modify | Fix `TokenService(db_session)` → `TokenService(RefreshTokenRepository(db, tenant_id))`. Add HTTP-endpoint assertions for login/forgot. |

## Interfaces / Contracts

No new public interfaces. Reuses existing:

```python
from app.core.encryption import hash_email_for_lookup, decrypt_pii
# login / forgot
h = hash_email_for_lookup(body.email)
result = await db.execute(
    select(Usuario)
    .where(Usuario.email_hash == h, Usuario.deleted_at.is_(None))
    .order_by(Usuario.created_at)
)
user = result.scalars().first()
```

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Integration | login + forgot succeed with repository-created (encrypted) user | Real DB. Fixture uses `UsuarioRepository.create()` so `email_hash` is set. POST endpoint, assert token / 202. |
| Integration | Cross-tenant duplicate email → no `MultipleResultsFound` | Create same email in two tenants via repo; POST login; assert 200 (deterministic first match) not 500. |
| Integration | Legacy NULL `email_hash` → 401 not 500 | Insert raw `Usuario` with NULL `email_hash`; POST login; assert 401. |
| Integration | Impersonation audit stores plaintext email | Trigger impersonation; assert `detalle["target_email"]` is plaintext (not base64). |

No DB mocks (rule #4). Fixtures build users through `UsuarioRepository.create()`; the
NULL-hash case is the one deliberate raw insert to reproduce the legacy state.

## Migration / Rollout

No migration required. Pure code change; rollback = revert auth.py + test edits (returns
to known-broken baseline, no data to undo).

## Open Questions

- [ ] Definitive cross-tenant collision policy: `.first()` is a stopgap — future tenant selector or subdomain-based login should replace ambiguous resolution.
- [ ] Operational follow-up: verify/re-run the 006 `email_hash` backfill per environment for legacy NULL-hash users.
- [ ] Q-02: extract login/forgot lookup into `AuthService` (cross-tenant variant) and split auth.py (586 LOC > 500).
- [ ] R-04 API prefix unification touches auth.py — sequence after this change.
