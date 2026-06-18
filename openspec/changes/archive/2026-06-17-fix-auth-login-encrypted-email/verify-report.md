# Verification Report: fix-auth-login-encrypted-email

> Change: `fix-auth-login-encrypted-email`
> Persistence mode: HYBRID (engram + openspec)
> TDD mode: STRICT (pytest)
> Verdict: **PASS**

## Test Execution Evidence (real)

Command:
```
export DATABASE_URL="postgresql+asyncpg://trace_user:trace_pass@localhost:5433/activia_trace"
.venv/bin/python -m pytest tests/test_auth.py tests/test_auth_c07.py -q
```

Result: **32 passed, 0 failed** (45 warnings, 29.11s).
- `tests/test_auth.py`: 19 passed
- `tests/test_auth_c07.py`: 13 passed

Full suite NOT run by instruction (~95 pre-existing failures in padron/programas/liquidaciones
are baseline-confirmed and out of scope for this change).

## Spec Compliance Matrix (9 scenarios → test → result)

| # | Spec Scenario | Covering Test | Result |
|---|---------------|---------------|--------|
| 1 | Successful login with encrypted-email user | test_auth_c07::test_login_with_encrypted_email_succeeds (+ test_auth::test_login_success_no_2fa) | PASS |
| 2 | Login with non-existent email — timing-safe 401 | test_auth_c07::test_login_nonexistent_email_returns_401_timing_safe (+ test_auth::test_login_nonexistent_email) | PASS |
| 3 | Login with correct email but wrong password | test_auth_c07::test_login_wrong_password_returns_401 (+ test_auth::test_login_wrong_password) | PASS |
| 4 | Cross-tenant login — same email in two tenants | test_auth_c07::test_login_cross_tenant_duplicate_no_500 | PASS |
| 5 | Login with NULL email_hash user — timing-safe 401 | test_auth_c07::test_login_null_email_hash_returns_401_not_500 | PASS |
| 6 | Forgot-password with existing user | test_auth_c07::test_forgot_existing_user_succeeds (+ test_auth::test_forgot_existing_email) | PASS |
| 7 | Forgot-password with non-existent email — anti-enumeration | test_auth_c07::test_forgot_nonexistent_email_anti_enumeration (+ test_auth::test_forgot_nonexistent_email) | PASS |
| 8 | Impersonation audit log contains readable email | test_auth_c07::test_impersonation_audit_stores_plaintext_email | PASS |
| 9 | Login test uses repository-created user (fixture is real) | test_auth::_create_test_user uses UsuarioRepository.create(); all login tests pass through ciphertext path | PASS |

All 9 spec scenarios are covered by a test that PASSED at runtime.

## Task Completion (24 tasks, all [x])

Spot-checked against code — implementation matches claims:
- 1.1/1.2: `_create_test_user()` uses `UsuarioRepository(db_session, tenant_id).create(...)`,
  no `tenant_id` kwarg to create(), single create() call (test_auth.py:42-51). VERIFIED.
- 2.1: `TokenService(RefreshTokenRepository(db, tenant_id))` (test_auth_c07.py:49-51). VERIFIED.
- 2.2-2.9: all 8 RED integration tests present and passing. VERIFIED.
- 3.1: imports `decrypt_pii, hash_email_for_lookup` from `app.core.encryption` (auth.py:16). VERIFIED.
- 3.2: login uses `hash_email_for_lookup` + `email_hash ==` + `.order_by(created_at)` +
  `.scalars().first()`; dummy-hash timing-safe path preserved (auth.py:134-148). VERIFIED.
- 3.3: forgot uses identical hash lookup (auth.py:251-257). VERIFIED.
- 3.4: impersonation wraps `decrypt_pii(target.email)` in try/except fallback before
  `record_audit` (auth.py:561-572). VERIFIED.
- 5.1/5.2/5.3: inline comments document email_hash rationale, .first() rationale (OQ-C07-02),
  Q-02 deferral, and Rule #11 debt (auth.py:123-133, 249-250, 556-560). VERIFIED.

## Hard Rules Compliance

| Rule | Status | Evidence |
|------|--------|----------|
| #4 Tests without DB mocks | PASS | Real ephemeral DB (port 5433); fixtures via UsuarioRepository.create() |
| #8 Identity from credentials | PASS | Login derives user from email_hash of body credentials, not URL/header identity |
| #9 Multi-tenancy row-level | PASS | Login is the documented cross-tenant exception (OQ-C07-02); all other queries tenant-scoped |
| #12 PII AES-256 never bypassed | PASS | Login queries email_hash (HMAC), never plaintext email; audit decrypts via decrypt_pii |
| #5 Pydantic extra='forbid' | PASS | All auth schemas set ConfigDict(extra="forbid") |
| #16 ≤500 LOC backend file | SUGGESTION (accepted debt) | auth.py = 602 LOC; pre-existing, deferred to Q-02 |

## R-01 / R-07 Resolution

- **R-01 (CRITICAL)**: RESOLVED. Login (auth.py:134-140) and forgot (auth.py:251-257) now
  query `email_hash == hash_email_for_lookup(body.email)` with `.scalars().first()` +
  `ORDER BY created_at`. Cross-tenant duplicate no longer raises MultipleResultsFound
  (test_login_cross_tenant_duplicate_no_500 PASS). NULL email_hash → timing-safe 401, not 500
  (test_login_null_email_hash_returns_401_not_500 PASS).
- **R-07 (HIGH)**: RESOLVED. Impersonation audit stores `decrypt_pii(target.email)` with
  legacy plaintext fallback (auth.py:561-572); audit detalle["target_email"] is plaintext,
  asserted not ciphertext (test_impersonation_audit_stores_plaintext_email PASS).

## Issues

### CRITICAL
None.

### WARNING
None.

### SUGGESTION
1. `auth.py` is 602 LOC (> 500, Rule #16). Conscious, documented debt deferred to Q-02
   (AuthService extraction + file split). Not a blocker for this hotfix; inline comments
   already reference Q-02. Design estimated 586; actual is 602 (+16 from the fix) — track in Q-02.
2. Business logic in router (Rule #11) — accepted hotfix debt, documented in spec/design/comments,
   deferred to Q-02.
3. Operational follow-up: re-run/verify migration 006 email_hash backfill per environment so
   legacy NULL-hash users become reachable (idempotent; not a code fix).

## Notes on Persistence
- Engram artifacts for spec/tasks/design/apply-progress were NOT found under the expected
  topic keys (HYBRID mode). Verification used the openspec files as source of truth, which
  are complete and authoritative. No apply-progress artifact existed in either backend;
  task completion was verified directly against code state instead.

## Final Verdict: PASS
