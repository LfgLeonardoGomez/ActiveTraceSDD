## Context

Los changes C-01 (foundation-setup) y C-02 (core-models-y-tenancy) están completos y archivados. El backend tiene FastAPI async, SQLAlchemy 2.0, Alembic, PostgreSQL, Pydantic v2 y la estructura de directorios de Clean Architecture en su lugar. El modelo de datos incluye `Tenant`, `User` (con `email`, `password_hash`, `tenant_id`, `deleted_at`) y tablas de rol/asignación, pero **no existe aún** el mecanismo de autenticación, sesión ni control de acceso.

La decisión arquitectónica ADR-001 (auth propio: email + password + 2FA TOTP, JWT access 15 min + refresh con rotación) ya está cerrada. Este change materializa esa decisión, bloqueando el acceso a todo endpoint de dominio hasta que esté operativo. Es el primer change **CRÍTICO** del camino crítico: cualquier defecto compromete la confidencialidad e integridad de todos los datos académicos.

## Goals / Non-Goals

**Goals:**
- Implementar autenticación segura con JWT (access corto + refresh con rotación) y resolución de identidad exclusivamente desde token verificado.
- Implementar 2FA TOTP opt-in por usuario con enroll, verify y gating en login.
- Implementar recuperación de contraseña con token criptográfico de un solo uso y expiración corta.
- Implementar rate limiting por IP + email en login para mitigar fuerza bruta.
- Proveer la dependencia `get_current_user` inyectable en todos los routers, derivando `user_id`, `tenant_id` y roles del JWT.
- Cubrir con tests ≥90% de reglas de negocio sobre base real (sin mocks de DB).

**Non-Goals:**
- SSO con Moodle (llega en Fase 2, portal del alumno).
- Impersonación (ADR-004, se define al implementar esa feature).
- RBAC completo con matriz en base de datos (se introduce en C-04; aquí solo se resuelven roles desde JWT para que C-04 tenga sobre qué operar).
- Frontend de login (es parte de C-21 frontend-shell-y-auth; aquí solo se entrega la API).
- Notificaciones por email real (se usa N8N/worker en C-17; aquí el token de recuperación se genera y expone como texto para que el worker lo consuma, o se loggea en dev).

## Decisions

### D-01: Librería JWT → `python-jose[cryptography]` con RS256 (HMAC256 en dev/test)
- **Rationale**: `python-jose` es madura, soporta JWS/JWT, y la variante con `cryptography` usa backends seguros. Para MVP usamos HS256 con `SECRET_KEY` de 32+ chars (simplifica ops sin infra de claves asimétricas). El claim set es mínimo: `sub` (user UUID), `tenant_id` (UUID), `roles` (lista de strings), `type` ("access" | "refresh"), `jti` (UUID del refresh token), `iat`, `exp`.
- **Alternativa**: `PyJWT` — similar, pero `python-jose` tiene mejor manejo de JWK si en el futuro migramos a RS256.

### D-02: Refresh token almacenado en PostgreSQL (no stateless)
- **Rationale**: El refresh token DEBE poder invalidarse (rotación + revocación). Un JWT stateless no permite revocación inmediata. Se almacena en tabla `refresh_tokens` con `token_hash` (SHA-256 del token raw, no del JWT), `user_id`, `tenant_id`, `expires_at`, `used_at`, `revoked_at`, `ip_address`, `user_agent`, `deleted_at` (soft delete). El token raw nunca se guarda en texto plano; solo su hash.
- **Alternativa**: Redis — más rápido para lookups, pero agrega infraestructura extra antes de que sea necesaria. Se reevaluará si el volumen de sesiones lo justifica.

### D-03: 2FA con `pyotp` (TOTP RFC 6238)
- **Rationale**: `pyotp` es la librería estándar en Python para TOTP/HOTP. El secreto se genera con `pyotp.random_base32()`, se almacena **cifrado con AES-256** en la tabla `two_factor_enrollments` (campo `encrypted_secret`), y se expone como QR (provisioning URI) solo durante el enroll. Un usuario con `is_2fa_enabled = true` debe pasar el gating antes de que se emita el par JWT.
- **Alternativa**: WebAuthn/FIDO2 — más seguro, pero complejidad de UX y soporte de dispositivos. Se considera para Fase 2.

### D-04: Rate limiting con implementación propia en middleware + repository
- **Rationale**: `slowapi` está bien, pero acopla a Limiter de Flask-heritage y requiere Redis. Implementamos un rate limiter basado en PostgreSQL: tabla `rate_limit_buckets` (clave compuesta `resource` + `window_start`) con contador atómico (`UPDATE ... RETURNING`). Es suficiente para el volumen inicial y evita agregar Redis solo por esto. El endpoint login usa clave `login:{ip}:{email}`.
- **Alternativa**: Redis + `slowapi` / `fastapi-limiter` — escala mejor, pero Redis es infra adicional. Se migra cuando el throughput lo justifique.

### D-05: Password reset token criptográfico aleatorio (no JWT)
- **Rationale**: El token de recuperación no necesita ser un JWT (no transporta claims de sesión). Generamos 32 bytes aleatorios vía `secrets.token_urlsafe()`, almacenamos su hash (SHA-256) en `password_reset_tokens` con `expires_at` (1 hora) y `used_at`. El email al usuario contiene el token raw (una sola vez). Al consumirlo, se verifica el hash y se marca `used_at`.
- **Alternativa**: JWT con claim `purpose: reset` — más complejo de validar y permite "re-validación" si no se revoca correctamente. Un token opaco es más simple y seguro.

### D-06: Argon2id via `passlib[argon2]`
- **Rationale**: `passlib` ya está en el stack (C-02 creó usuarios con password hash). Argon2id es el ganador del Password Hashing Competition y cumple con OWASP. Parámetros por defecto: tiempo=2, memoria=65536, paralelismo=4.

### D-07: `get_current_user` retorna un `CurrentUser` Pydantic model, no el ORM model
- **Rationale**: Evita que los routers toquen ORM directamente. El modelo `CurrentUser` tiene `id`, `tenant_id`, `roles`, `email` (desencriptado vía AES-256 si es necesario). Se usa `Annotated[CurrentUser, Depends(get_current_user)]` en endpoints.

## Risks / Trade-offs

| Risk | Mitigación |
|------|------------|
| **R-01**: Reuse de refresh token no detectado (rotación rota) | Tabla `refresh_tokens` guarda `used_at`. Si llega un refresh cuyo `used_at` ya está seteado → revocar toda la familia de tokens del usuario (logout global) y retornar 401. |
| **R-02**: Fuerza bruta sobre login | Rate limiting 5/60s por IP+email + retardo constante en verificación de password (Argon2id ya lo hace). Considerar captcha tras N bloqueos consecutivos en C-04. |
| **R-03**: Token de recuperación interceptado en tránsito | HTTPS/TLS 1.3 obligatorio en prod (ya en C-01). Expiración corta (1h). Single-use (used_at). |
| **R-04**: Secreto TOTP robado de base de datos | Cifrado AES-256 en reposo (`encrypted_secret`). El secreto raw solo existe en memoria durante el enroll (generación + render QR). |
| **R-05**: Timing attack en comparación de token hash | Usar `hmac.compare_digest()` para comparar hashes de tokens. |
| **R-06**: Secreto JWT comprometido (`SECRET_KEY`) | Rotación manual de `SECRET_KEY` requiere que todos los access tokens vigentes fallen (aceptable: 15 min de ventana). Automatizar rotación fuera del MVP. |

## Migration Plan

1. Ejecutar migración Alembic para crear tablas `refresh_tokens`, `password_reset_tokens`, `two_factor_enrollments`.
2. Agregar variables de entorno si no existen: `ACCESS_TOKEN_EXPIRE_MINUTES=15`, `REFRESH_TOKEN_EXPIRE_DAYS=7`.
3. Verificar que `SECRET_KEY` tenga ≥32 caracteres en todos los entornos.
4. Deploy del backend con los nuevos endpoints; no afecta endpoints existentes (solo agrega rutas bajo `/api/auth`).
5. Rollback: eliminar migración (downgrade Alembic) y revertir código del router auth. Los usuarios activos perderán sesión (aceptable para un change de auth inicial).

## Open Questions

- **OQ-01**: ¿Se envía el email de recuperación sincrónicamente desde el endpoint o se encola en el worker de comunicaciones (aún no existe)? → **Decisión** (2026-06-07): el endpoint genera el token y lo **loggea estructurado en consola** (modo dev). El envío real vía email/N8N se conecta en C-12 cuando existe el worker de comunicaciones.
- **OQ-02**: ¿El refresh token se transporta en cookie `HttpOnly` o en body JSON? → **Decisión** (2026-06-07): **cookie `HttpOnly` con `Secure` y `SameSite=Lax`** para mitigar XSS. El access token sigue en body JSON (la SPA lo guarda en memoria). El router `/api/auth/refresh` lee la cookie; `/api/auth/logout` limpia la cookie.
- **OQ-03**: ¿Se permite múltiples sesiones simultáneas por usuario? → **Decisión** (2026-06-07): **sí, sin límite en MVP**. Cada login emite un par independiente. El reuse de un refresh invalida solo esa familia (el refresh usado), no todas las sesiones del usuario.
