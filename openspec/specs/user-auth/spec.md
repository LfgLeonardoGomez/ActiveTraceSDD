# user-auth Specification

> Change: `fix-auth-login-encrypted-email`
> Capability: Modified — `user-auth`
> Hard rules validated: #4, #8, #9, #12

## Purpose

Defines the required behavior for user login, password-reset initiation, and
impersonation audit logging when the `email` column is stored as AES-256-GCM
ciphertext and lookups MUST use the deterministic `email_hash` column.

This is a full spec for the `user-auth` domain (no prior spec existed).

---

## Requirements

### Requirement: Login via email hash lookup

The system MUST look up the authenticating user by
`email_hash == hash_email_for_lookup(body.email)` and MUST NOT query the
ciphertext `email` column for equality.

The query MUST return at most one row using FIRST MATCH by `ORDER BY
created_at ASC` (not `scalar_one_or_none`), because the same email may exist
in multiple tenants (cross-tenant login is the documented exception
OQ-C07-02).

When no matching row is found (including when the user's `email_hash` is
NULL), the system MUST perform a timing-safe dummy password verification and
return HTTP 401 without indicating whether the email exists.

Validates: Rule #8 (identity from credentials, not URL/body), Rule #9
(login is the documented cross-tenant exception), Rule #12 (PII AES-256 never
bypassed).

#### Scenario: Successful login with encrypted-email user

- GIVEN a user created via `UsuarioRepository.create()` with a valid email and
  password (email stored as ciphertext, `email_hash` computed by the
  repository)
- WHEN `POST /api/auth/login` is called with the correct plaintext email and
  password
- THEN the response is HTTP 200
- AND the response body contains `access_token` and `refresh_token`

#### Scenario: Login with non-existent email — timing-safe 401

- GIVEN no user in the database has a matching `email_hash`
- WHEN `POST /api/auth/login` is called with any email
- THEN the response is HTTP 401
- AND the response does NOT reveal whether the email is registered

#### Scenario: Login with correct email but wrong password

- GIVEN a user exists with a matching `email_hash`
- WHEN `POST /api/auth/login` is called with that email and an incorrect
  password
- THEN the response is HTTP 401
- AND no token is issued

#### Scenario: Cross-tenant login — same email in two tenants

- GIVEN two users in different tenants share the same email (same `email_hash`)
- WHEN `POST /api/auth/login` is called with that email and the correct
  password for either user
- THEN the response is HTTP 200 (no `MultipleResultsFound` exception)
- AND the token corresponds to the user with the earlier `created_at`
  (first match, deterministic)

#### Scenario: Login with NULL email_hash user — timing-safe 401

- GIVEN a user row has `email_hash` NULL (legacy residual from failed backfill)
- WHEN `POST /api/auth/login` is called with any email
- THEN the response is HTTP 401
- AND the system does NOT raise an unhandled exception (no HTTP 500)
- AND the response is indistinguishable from a non-existent-user 401

---

### Requirement: Password reset initiation via email hash lookup

The system MUST look up the target user for `forgot_password` by
`email_hash == hash_email_for_lookup(body.email)` and MUST NOT query the
ciphertext `email` column.

When no matching row is found, the system MUST return a response
indistinguishable from the success response (anti-enumeration).

Validates: Rule #12 (PII respected), Rule #8 (no identity from body param
beyond credential flow).

#### Scenario: Forgot-password with existing user

- GIVEN a user created via `UsuarioRepository.create()` with a known email
- WHEN `POST /api/auth/forgot` is called with that email
- THEN the response is HTTP 200 (or 202)
- AND a password-reset token is generated and associated with the user

#### Scenario: Forgot-password with non-existent email — anti-enumeration

- GIVEN no user exists with a matching `email_hash`
- WHEN `POST /api/auth/forgot` is called with any email
- THEN the response is HTTP 200 (or 202)
- AND the response body is indistinguishable from the success case
- AND no token is created

---

### Requirement: Impersonation audit log stores plaintext email

The system MUST store the impersonated user's email in plaintext (decrypted)
in the audit log entry's `detalle` field. It MUST NOT store the raw
`target.email` ciphertext value.

Decryption MUST use `decrypt_pii(target.email)` with a try/except fallback
that logs the error and stores a safe sentinel (e.g., `"[unreadable]"`) if
decryption fails — following the pattern already established in
`dependencies.py`.

Validates: Rule #12 (PII displayed only after proper decryption), Rule #8
(audit uses identity from session context, not URL).

#### Scenario: Impersonation audit log contains readable email

- GIVEN an admin initiates impersonation of a target user whose email is
  stored as AES-256-GCM ciphertext
- WHEN `POST /api/auth/impersonate/{user_id}` is called
- THEN an audit log entry is created
- AND `detalle["target_email"]` contains the plaintext email string (e.g.,
  `"user@example.com"`)
- AND `detalle["target_email"]` does NOT contain a base64 or hex-encoded
  ciphertext string

---

### Requirement: Test fixtures use repository for user creation

All test fixtures that create users for authentication tests MUST use
`UsuarioRepository.create()` (which computes `email_hash` and stores `email`
as ciphertext). Direct ORM instantiation (`Usuario(email=plaintext, ...)`) is
PROHIBITED in auth test setup.

Tests MUST run against a real or ephemeral database. DB mocking is PROHIBITED.

Validates: Rule #4 (tests without DB mocks).

#### Scenario: Login test uses repository-created user

- GIVEN a test that verifies login
- WHEN the test's setup calls `UsuarioRepository.create()` to insert the user
- THEN the resulting `email` column contains ciphertext
- AND `email_hash` is non-NULL and equals `hash_email_for_lookup(email)`
- AND the login endpoint test passes (tests real production path, not the
  accidentally-matching plaintext path)

#### Scenario: Test would fail against old plaintext-query code

- GIVEN a repository-created user (ciphertext email, computed email_hash)
- WHEN the test runs against the pre-fix code (which queries
  `WHERE email == plaintext`)
- THEN the test FAILS (no match found → 401 instead of 200)
- AND this confirms the test covers the actual regression

---

## Constraints and Documented Debt

| Item | Status |
|------|--------|
| Business logic in router (Rule #11 violation) | Accepted for hotfix; deferred to Q-02 refactor |
| `auth.py` exceeds 500 LOC (Rule #16) | Pre-existing; Q-02 splits the file |
| Cross-tenant login resolves by `ORDER BY created_at` | Accepted policy; tenant selector is a future enhancement |
| NULL `email_hash` users remain unreachable | Documented; backfill is an operational follow-up (idempotent) |
