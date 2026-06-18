# Exploration: fix-auth-login-encrypted-email

> Phase: SDD explore · Artifact store: hybrid (engram topic `sdd/fix-auth-login-encrypted-email/explore` + this file)
> Source: verified audit findings R-01 (CRITICAL) and R-07 (HIGH) from `docs/AUDITORIA-FALLAS.md`.

## Scope

Fix two confirmed runtime breakages in authentication:
- **R-01 (CRITICAL)** — `login` and `forgot_password` query the encrypted `email` column with plaintext, so they never match a real user → login broken in production.
- **R-07 (HIGH)** — impersonation audit log stores ciphertext instead of a readable email.

## Current State (evidence)

**Encryption architecture (confirmed):**
- `usuarios.email` is AES-256-GCM ciphertext, **non-deterministic** (random 12-byte nonce per `encrypt_pii()` call).
- A separate deterministic column `email_hash` stores `HMAC-SHA256(ENCRYPTION_KEY, email.strip().lower())` (64-char hex), computed by `UsuarioRepository._encrypt_pii_fields()` on every write.

**R-01 confirmed:**
- `backend/app/api/v1/routers/auth.py:130-136` (`login`) and `:245-251` (`forgot_password`) run raw `select(Usuario).where(Usuario.email == body.email, ...)`. The column holds ciphertext → never matches a repository-created user. The router bypasses `UsuarioRepository` and `AuthService`.
- **Key discovery:** `AuthService.authenticate()` (`backend/app/services/auth_service.py:43`) already does it correctly via `repo.get_by_email_hash(email)`. It was implemented in C-07 but the HTTP router was never wired to it.

**Why tests don't catch it:**
- `tests/test_auth.py::_create_test_user()` (lines 23-43) creates users with `Usuario(email=email, ...)` directly, bypassing the repository → `email` gets plaintext, `email_hash` is NULL. The login query `WHERE email == plaintext` matches by accident. Physically impossible in production.
- `tests/test_auth_c07.py` uses the repository correctly but tests `AuthService` in isolation (not the HTTP endpoint) and instantiates `TokenService(db_session)` with the wrong constructor (it requires `RefreshTokenRepository`) → likely broken.

**R-07 confirmed:**
- `auth.py:556`: `detalle={"target_email": target.email}` where `target` is a raw ORM instance (email never decrypted). Correct pattern already exists in `dependencies.py:125-128` and `:151-154`.

**Cross-tenant login (documented debt):**
- Login is intentionally cross-tenant (no tenant selector on the form; documented as OQ-C07-02). The hash fix preserves this: `WHERE email_hash == hash AND deleted_at IS NULL`, no `tenant_id` filter.

## Candidate Approaches

| Approach | Pros | Cons | Effort |
|---|---|---|---|
| **A — Inline hash query in router** | Minimal change, low risk | Router keeps business logic (known debt) | Low |
| **B — Wire router to `AuthService.authenticate()`** | Architecturally clean, uses C-07 service as designed | Larger; needs cross-tenant path on service/repo; forgot still needs a lookup method | Medium |
| **C — Inline fix now + explicit defer of arch cleanup to Q-02** | Fast hotfix, debt made explicit | Same as A | Low |

## Recommendation

**Approach A/C (targeted hotfix), defer architectural cleanup to Q-02 (auth.py file split):**
1. `login()` + `forgot_password()`: replace raw `email == plaintext` with `email_hash == hash_email_for_lookup(body.email)`. Keep the timing-safe dummy-hash path for user-not-found (anti-enumeration).
2. `start_impersonation()`: wrap `target.email` with `decrypt_pii(...)` (try/except fallback, matching `dependencies.py`).
3. Repair `test_auth.py::_create_test_user()` to go through `UsuarioRepository.create()` → existing tests become real regression tests.
4. Fix `test_auth_c07.py` `TokenService` constructor.
5. Add regression tests hitting the HTTP endpoints with repository-created users.

## Affected Files & Blast Radius

- `backend/app/api/v1/routers/auth.py` — login, forgot_password, impersonation log. **Already 586 LOC** (violates ≤500 hard rule).
- `backend/tests/test_auth.py` — fixture stores plaintext email.
- `backend/tests/test_auth_c07.py` — wrong `TokenService` constructor; no HTTP coverage.
- `backend/app/services/auth_service.py` — already correct; no change for hotfix.
- `backend/app/repositories/usuarios.py` — `get_by_email_hash()` already exists; no change.

## Risks & Open Questions (for propose phase)

1. **Cross-tenant `email_hash` uniqueness** — verify migration `006_usuario_pii_asignacion.py`: is there a global unique index on `email_hash`, or only `(tenant_id, email_hash)`? If tenant-scoped, two tenants sharing an email make `scalar_one_or_none()` raise `MultipleResultsFound` at login.
2. **Legacy users with NULL `email_hash`** — verify the C-07 backfill data-migration ran; NULL-hash users become unreachable after the fix.
3. **`auth.py` LOC** — fix adds ~15 lines to an already-oversized file; Q-02 split is a mandatory follow-up.
4. **R-04 coordination** — prefix unification also edits `auth.py`. Per `docs/PLAN-REMEDIACION.md`: R-01+R-07 first, then R-04. Same owner, sequential.

## Hard Rules in Play

- Identity always from session (JWT) — login is the one cross-tenant entry point by design.
- PII encrypted AES-256; passwords Argon2id; lookups via deterministic `email_hash`.
- Multi-tenancy row-level (login is the documented cross-tenant exception).
- ≤500 LOC backend file (auth.py already over → Q-02 follow-up).
- Tests with real/ephemeral DB, no DB mocks; Strict TDD if active.

## Next

`sdd-propose` — formalize the hotfix proposal. Resolve risks #1 and #2 (inspect migration `006`) during propose.
