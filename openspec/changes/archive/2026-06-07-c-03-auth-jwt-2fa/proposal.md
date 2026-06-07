## Why

activia-trace necesita un sistema de autenticación propio, robusto y multi-tenant antes de que cualquier usuario pueda operar sobre datos académicos sensibles. Los dos changes anteriores (C-01 foundation-setup y C-02 core-models-y-tenancy) dejaron la infraestructura y el modelo de datos listos, pero aún no existe mecanismo de login, sesión ni control de acceso. Sin auth, los endpoints de dominio no pueden protegerse, el aislamiento de tenant no tiene efecto práctico y toda la plataforma permanece inoperable para usuarios finales. Además, la decisión arquitectónica ADR-001 (auth propio con JWT + refresh rotation + 2FA TOTP) ya está cerrada, por lo que este change materializa esa decisión.

## What Changes

- **Nuevo módulo `auth`** en el backend con endpoints dedicados:
  - `POST /api/auth/login` — validación de credenciales (email + password con Argon2id) y emisión de par JWT (access 15 min + refresh token con rotación).
  - `POST /api/auth/refresh` — rotación de refresh token: un refresh usado se invalida inmediatamente y se emite un nuevo par access + refresh.
  - `POST /api/auth/logout` — revocación explícita de la sesión (marcado del refresh token como usado/revocado).
  - `POST /api/auth/forgot` — solicitud de recuperación de contraseña con token de un solo uso y corta expiración enviado por email.
  - `POST /api/auth/reset` — restablecimiento de contraseña consumando el token de recuperación.
- **2FA TOTP opcional por usuario**: enroll (generación de secreto + QR), verify (validación de código TOTP) y gating entre validación de credenciales e emisión de sesión.
- **Rate limiting** en login: 5 intentos por ventana de 60 segundos, claveada por IP + email.
- **Dependencia `get_current_user`** para inyección en routers: resuelve identidad (`user_id`), `tenant_id` y roles **exclusivamente** desde el JWT verificado. Ningún parámetro de request puede alterar la identidad.
- **Modelos y repositorios** para `RefreshToken`, `PasswordResetToken` y `TwoFactorEnrollment`, con soft delete (`deleted_at`) y scope de `tenant_id`.
- **Tests** sin mocks de DB: flujo login OK/KO, rotación de refresh (reuse invalida), flujo 2FA completo, recuperación con single-use token, rate limit y prueba de que la identidad no puede ser mutada por parámetros externos.

## Capabilities

### New Capabilities
- `jwt-auth`: Autenticación con JWT de vida corta (access token) + refresh token con rotación, revocación y resolución de identidad desde sesión.
- `totp-2fa`: Autenticación de segundo factor (TOTP) opt-in por usuario, con enroll, verify y gating en el flujo de login.
- `password-recovery`: Recuperación de contraseña por email con token criptográfico de un solo uso y expiración corta.
- `rate-limiting`: Rate limiting por IP + email en endpoints de autenticación para mitigar fuerza bruta.

### Modified Capabilities
- *(Ninguno — este change no modifica capabilities existentes.)*

## Impact

- **Backend**: nuevo router `auth`, servicios `auth_service`, `token_service`, `two_factor_service`, repositorios `refresh_token_repository`, `password_reset_token_repository`, `two_factor_repository`, y módulo `core/security.py` (JWT, Argon2id, AES-256).
- **Base de datos**: nuevas tablas `refresh_tokens`, `password_reset_tokens`, `two_factor_enrollments`; migración Alembic dedicada.
- **Frontend**: el cliente HTTP (`api.ts`) debe implementar interceptor de refresh automático ante 401 por token expirado.
- **Dependencias**: `python-jose[cryptography]`, `passlib[argon2]`, `pyotp`, `slowapi` (o implementación propia de rate limiting), `cryptography`.
- **Seguridad**: este change es **CRÍTICO** — cualquier defecto en JWT, rotación de refresh o 2FA compromete toda la plataforma. Requiere revisión humana obligatoria antes de merge.
