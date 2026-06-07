## 1. Setup y Migraciones

- [ ] 1.1 Agregar dependencias: `python-jose[cryptography]`, `passlib[argon2]`, `pyotp`, `cryptography`; verificar `slowapi` o definir rate limiter propio.
- [ ] 1.2 Actualizar `backend/app/core/config.py` con variables: `ACCESS_TOKEN_EXPIRE_MINUTES=15`, `REFRESH_TOKEN_EXPIRE_DAYS=7`, `SECRET_KEY` (≥32 chars), `ENCRYPTION_KEY` (32 chars).
- [ ] 1.3 Crear migración Alembic para tablas: `refresh_tokens`, `password_reset_tokens`, `two_factor_enrollments`, `rate_limit_buckets`.
- [ ] 1.4 Verificar que todas las tablas nuevas tengan `tenant_id`, `created_at`, `updated_at`, `deleted_at`.

## 2. Módulo de Seguridad Core

- [ ] 2.1 Implementar `backend/app/core/security.py`:
  - `create_access_token(user_id, tenant_id, roles, expires_delta)` → JWT firmado (HS256, claims mínimos).
  - `create_refresh_token()` → token opaco aleatorio (32 bytes URL-safe).
  - `verify_access_token(token)` → decodificación y validación de firma/exp.
  - `verify_password(plain, hashed)` y `hash_password(plain)` via Argon2id (`passlib`).
  - `encrypt_aes256(plaintext)` / `decrypt_aes256(ciphertext)` para PII/secrets (usa `ENCRYPTION_KEY`).
- [ ] 2.2 Implementar `create_pre_auth_token(user_id, tenant_id)` para gating 2FA (expiración 5 min, claim `type: pre_auth`).

## 3. Modelos ORM

- [ ] 3.1 Crear `backend/app/models/refresh_token.py`: `RefreshToken` con `token_hash`, `user_id`, `tenant_id`, `expires_at`, `used_at`, `revoked_at`, `ip_address`, `user_agent`, `deleted_at`.
- [ ] 3.2 Crear `backend/app/models/password_reset_token.py`: `PasswordResetToken` con `token_hash`, `user_id`, `tenant_id`, `expires_at`, `used_at`, `deleted_at`.
- [ ] 3.3 Crear `backend/app/models/two_factor_enrollment.py`: `TwoFactorEnrollment` con `user_id`, `tenant_id`, `encrypted_secret`, `status` (pending/confirmed), `deleted_at`.
- [ ] 3.4 Crear `backend/app/models/rate_limit_bucket.py`: `RateLimitBucket` con `resource`, `window_start`, `count`, `created_at`.

## 4. Repositories

- [ ] 4.1 Crear `backend/app/repositories/refresh_token_repository.py`:
  - `create(token_hash, user_id, tenant_id, expires_at, ip, ua)` → insert con scope de tenant.
  - `get_by_token_hash(token_hash)` → filtra por tenant y `deleted_at is null`.
  - `mark_used(token_hash)` → `UPDATE used_at = now()`.
  - `revoke_all_for_user(user_id, tenant_id)` → `UPDATE revoked_at = now()` para tokens vigentes.
- [ ] 4.2 Crear `backend/app/repositories/password_reset_token_repository.py`:
  - `create(token_hash, user_id, tenant_id, expires_at)`.
  - `get_by_token_hash(token_hash)` → scope tenant + `deleted_at is null`.
  - `mark_used(token_hash)`.
- [ ] 4.3 Crear `backend/app/repositories/two_factor_repository.py`:
  - `create_or_get(user_id, tenant_id)`.
  - `update_secret(user_id, tenant_id, encrypted_secret)`.
  - `confirm(user_id, tenant_id)` → setea `status = confirmed`.
  - `get_active_for_user(user_id, tenant_id)` → filtra `deleted_at is null`.
  - `soft_delete_for_user(user_id, tenant_id)`.
- [ ] 4.4 Crear `backend/app/repositories/rate_limit_repository.py`:
  - `increment(resource, window_start)` → `UPDATE ... RETURNING count` (o insert + on conflict).
  - `get_count(resource, window_start)`.
  - `cleanup_old_windows(before)` → borra buckets antiguos.
- [ ] 4.5 Verificar que **todos** los queries apliquen scope de `tenant_id` por defecto (regla dura #9).

## 5. Servicios de Dominio

- [ ] 5.1 Crear `backend/app/services/token_service.py`:
  - `issue_token_pair(user, ip, ua)` → access JWT + refresh opaco; persiste refresh hash.
  - `rotate_refresh_token(raw_refresh, ip, ua)` → valida hash, marca used, emite nuevo par (detección de reuse → revoke all + raise 401).
  - `revoke_refresh_token(raw_refresh)` → marca `revoked_at`.
- [ ] 5.2 Crear `backend/app/services/auth_service.py`:
  - `authenticate(email, password, tenant_id)` → busca usuario por email en tenant, verifica Argon2id, retorna usuario.
  - `logout(raw_refresh)` → revoca token.
  - `get_current_user_dependency` → lógica compartida para `get_current_user`.
- [ ] 5.3 Crear `backend/app/services/two_factor_service.py`:
  - `enroll(user)` → genera secreto, cifra con AES-256, genera provisioning URI y QR base64.
  - `confirm_enroll(user, code)` → valida código contra secreto descifrado, activa flag, genera y almacena hashes de 10 backup codes.
  - `verify_totp(user, code)` → valida TOTP contra secreto descifrado.
  - `verify_backup_code(user, code)` → valida hash de backup code, marca usado.
  - `disable_2fa(user, code)` → verifica TOTP, soft-deletea enrollment, invalida backup codes.
- [ ] 5.4 Crear `backend/app/services/rate_limit_service.py`:
  - `check_limit(resource, max_requests, window_seconds)` → incrementa contador y retorna permitido/bloqueado + `Retry-After`.
  - `build_resource_key(endpoint, ip, email)` → normaliza clave.

## 6. Router Auth y Endpoints

- [ ] 6.1 Crear `backend/app/api/v1/routers/auth.py` con los siguientes endpoints y schemas Pydantic (`extra='forbid'` en todos):
  - `POST /api/auth/login` → `LoginRequest` (email, password); respuesta `TokenResponse` (access, refresh) o `PreAuthResponse` (pre_auth_token) si 2FA.
  - `POST /api/auth/refresh` → lee refresh token de **cookie `HttpOnly`**; respuesta `TokenResponse` (nuevo access en body, nuevo refresh en cookie `HttpOnly`).
  - `POST /api/auth/logout` → lee refresh token de cookie `HttpOnly`; limpia la cookie (set cookie vacío con max-age=0); 204.
  - `POST /api/auth/forgot` → `ForgotRequest` (email); 202 (comportamiento idéntico existente/inexistente).
  - `POST /api/auth/reset` → `ResetRequest` (token, new_password); 204 o error.
  - `POST /api/auth/2fa/enroll` → respuesta QR + URI (requiere auth).
  - `POST /api/auth/2fa/enroll/confirm` → `TwoFactorConfirmRequest` (code); respuesta backup codes.
  - `POST /api/auth/2fa/verify` → `TwoFactorVerifyRequest` (pre_auth_token, code); respuesta `TokenResponse`.
  - `POST /api/auth/2fa/disable` → `TwoFactorDisableRequest` (code); 204.
- [ ] 6.2 Aplicar rate limiting en `login`, `forgot`, `2fa/verify` usando `RateLimitService`.
- [ ] 6.3 Manejar errores estandarizados: 400 validación, 401 auth, 403 authz (placeholder), 404 no encontrado, 429 rate limit, 500 interno.

## 7. Dependencias de Inyección

- [ ] 7.1 Implementar `backend/app/core/dependencies.py`:
  - `get_current_user(token: Annotated[str, Depends(oauth2_bearer)])` → decodifica JWT, busca usuario en DB (scope tenant), retorna `CurrentUser` Pydantic model.
  - `get_current_active_user` → wrapper que verifica `deleted_at is null`.
  - `require_permission(permission: str)` → placeholder que retorna 403; se completará en C-04.
- [ ] 7.2 Verificar que `get_current_user` NUNCA use parámetros de request (URL, body, header custom) para identidad (regla dura #8).

## 8. Tests

- [ ] 8.1 Tests de login:
  - Login exitoso sin 2FA → retorna access + refresh.
  - Login fallido (password incorrecta) → 401, no emite tokens.
  - Login con email inexistente → 401, comportamiento idéntico en tiempo.
- [ ] 8.2 Tests de refresh rotation:
  - Refresh exitoso → nuevo access + nuevo refresh, anterior marcado used.
  - Reuse de refresh → 401, todos los refresh del usuario revocados (logout global).
  - Refresh expirado → 401.
- [ ] 8.3 Tests de 2FA:
  - Enroll genera QR y secreto cifrado.
  - Confirm con código válido → activa 2FA, retorna backup codes.
  - Confirm con código inválido → 400, no activa.
  - Login con 2FA habilitado → 202 + pre_auth_token; verify correcto → tokens; verify incorrecto → 401.
  - Uso de backup code → login exitoso, código marcado usado.
  - Disable 2FA → soft-delete enrollment.
- [ ] 8.4 Tests de recuperación:
  - Forgot con email existente → token generado; forgot con inexistente → 202 idéntico.
  - Reset con token válido → password cambiada, refresh tokens revocados.
  - Reset con token expirado → 400, password sin cambio.
  - Reset con token usado → 400, password sin cambio.
- [ ] 8.5 Tests de rate limiting:
  - 5 intentos login permitidos; 6to → 429.
  - Buckets independientes por IP+email.
  - Header `Retry-After` presente.
- [ ] 8.6 Tests de identidad inmutable por parámetro:
  - Endpoint protegido recibe body con `user_id`/`tenant_id` distintos; el sistema opera con identidad del JWT, ignora parámetros.
  - Token manipulado → 401.
- [ ] 8.7 Alcance: ≥90% de reglas de negocio cubiertas. Sin mocks de DB (usa test DB real).

## 9. Documentación y Verificación

- [ ] 9.1 Actualizar `AGENTS.md` si hay cambios en convenciones de auth (no tocar reglas duras globales).
- [ ] 9.2 Verificar que todos los schemas Pydantic usen `model_config = ConfigDict(extra='forbid')`.
- [ ] 9.3 Ejecutar `pytest` y asegurar que todos los tests pasan.
- [ ] 9.4 Ejecutar `alembic upgrade head` en contenedor de test y verificar integridad de migraciones.
- [ ] 9.5 Revisión de seguridad: checklist de R-01 a R-06 del design.md (rotación, rate limit, tokens single-use, 2FA cifrado, timing attacks, secreto JWT).
