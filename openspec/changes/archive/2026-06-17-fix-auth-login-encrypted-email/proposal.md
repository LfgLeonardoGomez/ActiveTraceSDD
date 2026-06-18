# Proposal: Fix login/forgot lookup against AES-encrypted email + readable impersonation audit

## Intent

Restore functional `login` and `forgot_password` (broken in production because they query the AES-256-GCM ciphertext `email` column, which never matches) and make impersonation audit logs human-readable.

## Scope

### In Scope
- **R-01 (CRITICAL)**: Fix `login` (auth.py:130-136) and `forgot_password` (auth.py:245-251) to look up by deterministic `email_hash == hash_email_for_lookup(email)` instead of `Usuario.email == body.email`.
- **R-07 (HIGH)**: Decrypt `target.email` via `decrypt_pii()` (with legacy fallback) before writing it to the impersonation audit log (auth.py:556).
- Cross-tenant duplicate handling for login (use `.scalars().first()` + deterministic ordering, NOT `scalar_one_or_none()`), preserving documented cross-tenant login behavior (OQ-C07-02).
- Fix false-positive test fixtures: `test_auth.py::_create_test_user()` must use `UsuarioRepository.create()` so `email` is ciphertext and `email_hash` is computed. Fix `test_auth_c07.py` `TokenService(db_session)` -> correct `RefreshTokenRepository` constructor.
- Add regression tests: login + forgot with PII-encrypted user; audit log asserts plaintext email.

### Out of Scope
- Architectural cleanup (moving lookup into `AuthService`) and the auth.py file split — deferred to **Q-02** (auth.py already at 586 LOC).
- API prefix unification — that is **R-04** (separate change, also touches auth.py).
- Backfilling legacy `email_hash` data — see Risk Resolution 2 (documented, no migration needed for this change).

## Capabilities

### New Capabilities
- None

### Modified Capabilities
- `user-auth`: login and password-reset lookup behavior changes from plaintext-email match to encrypted-email hash lookup; cross-tenant duplicate-email resolution policy defined; impersonation audit detail now stores plaintext email.

## Approach

**Chosen: Approach A/C (targeted inline hash fix), not Approach B (wire AuthService).**

Replace the raw `WHERE Usuario.email == body.email` with `WHERE Usuario.email_hash == hash_email_for_lookup(body.email)` directly in the router, keeping the documented cross-tenant search. Decrypt the matched user's email when needed downstream. Apply `decrypt_pii(target.email)` (try/except fallback per dependencies.py:125-128) for the audit log.

**Tradeoff**: This leaves business logic in the router (violates hard rule #11), but it is a CRITICAL production hotfix in a CRITICAL domain. Approach B (cross-tenant `AuthService` variant) is larger and riskier for a hotfix; it belongs in the Q-02 refactor that reorganizes the router anyway. We accept the known debt and document the follow-up explicitly.

## Risk Resolution (investigated with evidence)

**1. Cross-tenant uniqueness of `email_hash` — RESOLVED.**
`006_usuario_pii_asignacion.py:110-116` creates `idx_usuarios_tenant_email_hash` as UNIQUE on **`(tenant_id, email_hash)`** (partial, `WHERE deleted_at IS NULL`) — it is **tenant-scoped, NOT global**. The HMAC is keyed only by `ENCRYPTION_KEY` (lines 50-53), so the same email in two tenants yields the **same** hash and is permitted by the index. A cross-tenant login query can therefore return **multiple rows**, and the current code's `scalar_one_or_none()` (auth.py:136) would raise `MultipleResultsFound`. **Decision**: login uses `.scalars().first()` with a stable `ORDER BY created_at` (NOT `scalar_one_or_none`), authenticating against the first match. This preserves the documented cross-tenant login (no tenant selector exists yet) and avoids the crash. The collision policy and a future tenant selector are flagged for spec/design.

**2. Legacy users with NULL `email_hash` — RESOLVED (documented, no new migration).**
`006:82-105` DOES backfill `email_hash` for existing users, but the backfill is wrapped in a bare `except: pass` (lines 102-104): if `ENCRYPTION_KEY` was unavailable at migration time it silently skips, and users whose email was already ciphertext are skipped by the `_is_ciphertext` guard (line 93). So NULL `email_hash` is a possible residual state. **Decision**: no backfill migration is added in this hotfix — the deterministic HMAC is stable, so backfill is **idempotent and safe to run later**, but it is operational/data concern, not a code fix, and adding a migration broadens this CRITICAL hotfix. The login fix tolerates NULL `email_hash` gracefully (no match -> standard 401 with timing-safe dummy verify, preserving R2 anti-enumeration). The need to verify/re-run backfill in each environment is documented as an operational follow-up.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/api/v1/routers/auth.py` | Modified | R-01 (login:130-136, forgot:245-251), R-07 (impersonate:556). +~15 LOC; file already 586 (rule #16) -> pair with Q-02 split |
| `backend/tests/test_auth.py` | Modified | `_create_test_user()` use repository; tests become real-path |
| `backend/tests/test_auth_c07.py` | Modified | Fix `TokenService` constructor; add HTTP-endpoint assertions |

## Hard Rules in play

- #8 Identity from session — unchanged (login derives identity from credentials, not URL/body).
- #9 Multi-tenancy row-level — **login is the documented cross-tenant exception** (OQ-C07-02); all other paths stay tenant-scoped.
- #11 No business logic in routers — knowingly deferred to Q-02 (documented debt).
- #12 PII AES-256 — the fix respects encryption (hash lookup + decrypt for display), never bypasses it.
- #16 ≤500 LOC — auth.py at 586 already over; must pair with Q-02 split. Tests without DB mocks (#4) — all new tests use real DB.

## Governance

Domain = **auth = CRITICAL**. Per Agent Governance, this change requires **explicit human approval before implementation**. Propose-only until approved.

## Coordination

**R-04 (API prefix unification) also touches auth.py.** Per PLAN-REMEDIACION ("un solo dueño, en orden: R-01→R-07→prefix→split"), this change goes **first and sequentially**; R-04 and the Q-02 split follow. No PRs/branching (local + engram/openspec delivery).

## Rollback Plan

Pure code change, no schema migration. Revert the auth.py and test edits to restore prior state. The (broken) prior login is non-functional in prod anyway, so rollback only returns to the known-broken baseline; no data migration to undo.

## Success Criteria

- [ ] A user created via `UsuarioRepository.create()` (ciphertext email, computed `email_hash`) can `POST /api/auth/login` and receive an access token.
- [ ] `POST /api/auth/forgot` finds the same user and issues a reset token.
- [ ] Cross-tenant duplicate email does NOT raise `MultipleResultsFound`; login authenticates a deterministic match.
- [ ] Impersonation audit `detalle["target_email"]` contains plaintext email (no base64 ciphertext).
- [ ] Legacy NULL-`email_hash` user produces a normal 401 (timing-safe), not a 500.
- [ ] `test_auth.py` and `test_auth_c07.py` pass against a real DB and would fail under the old code (true regression coverage).
