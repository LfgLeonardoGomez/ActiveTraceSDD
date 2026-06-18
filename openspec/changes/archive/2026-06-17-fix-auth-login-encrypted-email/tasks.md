# Tasks: Fix Auth Login — Encrypted Email Lookup + Impersonation Audit

> Change: `fix-auth-login-encrypted-email`
> Test runner: `pytest` (asyncio_mode=auto, testpaths=["tests"])
> TDD mode: STRICT — each unit follows RED → GREEN → REFACTOR

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~120–160 (additions + deletions) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single atomic change (3 files) |
| Delivery strategy | no PRs (local fix) |
| Chain strategy | N/A |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Notes |
|------|------|-------|
| 1 | Test fixture repair + regression RED tests | All auth tests turn real (may go red) |
| 2 | Production fix in auth.py | Makes RED tests GREEN |
| 3 | Triangulation + suite verification | Confirm no false positives remain |

---

## Phase 1: Test Fixture Repair (turn existing tests into real tests)

> Goal: make test helpers use the repository so `email_hash` is computed. Tests that
> relied on plaintext-email matches will now be RED — that is the desired outcome.

- [x] 1.1 In `backend/tests/test_auth.py`, locate `_create_test_user()` and replace direct
  `Usuario(email=plaintext, ...)` ORM instantiation with
  `await UsuarioRepository(db_session, tenant_id).create(...)`. Confirm import of
  `UsuarioRepository` from `app.repositories.usuarios`.
- [x] 1.2 Verify that `_create_test_user()` does NOT pass `tenant_id` as a keyword to
  `repo.create()` (the repo injects it internally; passing it raises `ValueError`).
  NOTE: all fields passed in single create() call to avoid dirty-write bug (UsuarioRepository
  decrypts instance in-place; a second commit flushes plaintext back to DB).
- [x] 1.3 Run `pytest backend/tests/test_auth.py -x` against the UNMODIFIED `auth.py` and
  confirm that login-related tests now FAIL with 401 (RED). This confirms fixtures are real.

---

## Phase 2: Fix `test_auth_c07.py` Constructor + Add RED HTTP Assertions

> Goal: repair the broken `TokenService` constructor and add endpoint-level assertions
> that will be RED until auth.py is fixed.

- [x] 2.1 In `backend/tests/test_auth_c07.py`, replace `TokenService(db_session)` with
  `TokenService(RefreshTokenRepository(db, tenant_id))`. Confirm both imports are present.
- [x] 2.2 Add RED integration test: `test_login_with_encrypted_email_succeeds` — creates a
  user via `UsuarioRepository.create()`, POSTs to `POST /api/auth/login` with correct
  credentials, asserts HTTP 200 + `access_token` in response body.
  Spec scenario: `Successful login with encrypted-email user`.
- [x] 2.3 Add RED integration test: `test_login_nonexistent_email_returns_401_timing_safe`
  — POST to login with email that has no matching `email_hash`, assert HTTP 401.
  Spec scenario: `Login with non-existent email — timing-safe 401`.
- [x] 2.4 Add RED integration test: `test_login_wrong_password_returns_401` — user exists
  (repo-created), POST login with wrong password, assert HTTP 401 + no token.
  Spec scenario: `Login with correct email but wrong password`.
- [x] 2.5 Add RED integration test: `test_login_cross_tenant_duplicate_no_500` — same
  email created in two tenants via `UsuarioRepository.create()` for each tenant; POST login;
  assert HTTP 200 (not 500, no `MultipleResultsFound`).
  Spec scenario: `Cross-tenant login — same email in two tenants`.
- [x] 2.6 Add RED integration test: `test_login_null_email_hash_returns_401_not_500` —
  insert one `Usuario` row with `email_hash=NULL` via raw ORM (deliberate legacy state);
  POST login with that email; assert HTTP 401 (not 500).
  Spec scenario: `Login with NULL email_hash user — timing-safe 401`.
- [x] 2.7 Add RED integration test: `test_forgot_existing_user_succeeds` — repo-created
  user; POST `POST /api/auth/forgot` with their email; assert HTTP 200 or 202 + reset
  token created.
  Spec scenario: `Forgot-password with existing user`.
- [x] 2.8 Add RED integration test: `test_forgot_nonexistent_email_anti_enumeration` —
  no matching user; POST forgot; assert HTTP 200 or 202 (same shape as success).
  Spec scenario: `Forgot-password with non-existent email — anti-enumeration`.
- [x] 2.9 Add RED integration test: `test_impersonation_audit_stores_plaintext_email` —
  trigger `POST /api/auth/impersonate/{user_id}`; query audit log; assert
  `detalle["target_email"]` is a valid email string (not base64/hex ciphertext).
  Spec scenario: `Impersonation audit log contains readable email`.
- [x] 2.10 Run `pytest backend/tests/test_auth_c07.py -x` and confirm all new tests FAIL
  (RED). Confirm existing tests also FAIL due to fixture repair from Phase 1.

---

## Phase 3: Production Fix — `auth.py` (GREEN)

> Goal: minimal code change in `auth.py` that satisfies all RED tests. No architectural
> changes; defer Q-02 split and R-04 prefix work.

- [x] 3.1 In `backend/app/api/v1/routers/auth.py`, add `hash_email_for_lookup` and
  `decrypt_pii` to the import from `app.core.encryption` (line ~4-10 imports block).
- [x] 3.2 **Login lookup (lines 130-136)**: replace `WHERE Usuario.email == body.email`
  with the hash-based query:
  ```python
  h = hash_email_for_lookup(body.email)
  result = await db.execute(
      select(Usuario)
      .where(Usuario.email_hash == h, Usuario.deleted_at.is_(None))
      .order_by(Usuario.created_at)
  )
  user = result.scalars().first()
  ```
  Do NOT change the downstream timing-safe dummy-hash path (lines 138-144).
- [x] 3.3 **Forgot lookup (lines 245-251)**: apply identical hash-based replacement.
  Same pattern: `hash_email_for_lookup`, `.scalars().first()`, `ORDER BY created_at`,
  `deleted_at IS NULL`. Do NOT alter the anti-enumeration return branch.
- [x] 3.4 **Impersonation audit (line ~556)**: wrap `target.email` decryption before
  `record_audit`:
  ```python
  try:
      plain_email = decrypt_pii(target.email)
  except Exception:
      plain_email = target.email  # legacy plaintext fallback
  # then pass plain_email into record_audit detalle
  ```
  Follow the pattern from `dependencies.py:125-128,151-154`.
- [x] 3.5 Run `pytest backend/tests/test_auth.py backend/tests/test_auth_c07.py` and
  confirm ALL tests pass (GREEN). Zero failures expected at this point.

---

## Phase 4: Triangulation + Coverage Verification

> Goal: confirm no false positives survive and coverage thresholds are met.

- [x] 4.1 **Triangulation — fixture specificity**: temporarily revert auth.py login lookup
  back to `WHERE Usuario.email == body.email` in a local scratch; rerun the test suite and
  confirm tests from 2.2 and 2.5 FAIL. Restore the fix. This proves tests are not
  accidentally passing.
- [x] 4.2 Run `pytest backend/tests/test_auth.py backend/tests/test_auth_c07.py
  --cov=app/api/v1/routers/auth --cov-report=term-missing` and confirm:
  - Login hash-lookup branch: covered.
  - Forgot hash-lookup branch: covered.
  - Impersonation decrypt try/except both arms: covered (success path + except path).
  - Coverage ≥ 80% lines, ≥ 90% business-rule branches on auth module.
- [x] 4.3 Run the full test suite `pytest` to confirm no regressions outside the auth
  module. All previously passing tests must still pass.

---

## Phase 5: Cleanup and Debt Notation

> Goal: leave a clean, documented baseline for follow-up changes.

- [x] 5.1 Add or update inline comment block at the top of the modified section in
  `auth.py` (login + forgot) documenting:
  - Why `email_hash` is used instead of `email`.
  - Why `.scalars().first()` instead of `scalar_one_or_none()` (cross-tenant OQ-C07-02).
  - Reference to Q-02 for the planned `AuthService` extraction.
- [x] 5.2 Add a TODO comment at the impersonation decrypt block referencing Q-02 for
  extracting this into a service.
- [x] 5.3 Confirm that neither R-04 (API prefix unification) nor Q-02 (auth.py split) are
  started in this change — document them explicitly as deferred in a code comment or PR
  description note.

---

## Dependency Order

```
Phase 1 (fixture repair)
    └── Phase 2 (RED tests) — can start in parallel with Phase 1 after 1.1-1.2 complete
            └── Phase 3 (GREEN production fix) — blocked on Phase 2 RED tests existing
                    └── Phase 4 (triangulation) — blocked on Phase 3 passing
                            └── Phase 5 (cleanup) — non-blocking, run after Phase 4
```

Phases 1 and 2 (up to task 2.1) are sequential. Tasks 2.2-2.9 can be written in any order.
Phase 3 is strictly blocked on Phase 2 (tests must be RED before implementing the fix).

## Deferred Items (NOT in scope)

- **R-04**: API prefix unification (touches auth.py — sequence AFTER this change)
- **Q-02**: Extract login/forgot into `AuthService` + split `auth.py` (>500 LOC)
- **Backfill migration**: `email_hash` NULL users remain unreachable (operational follow-up)
- **Cross-tenant collision policy**: `.first()` is stopgap; tenant selector = future work
