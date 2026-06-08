### Requirement: Emisión de tokens JWT de acceso y refresco tras login válido
El sistema SHALL emitir un par de tokens (access token + refresh token) cuando el usuario proporciona credenciales válidas (email + password) y, si aplica, supera el segundo factor.

#### Scenario: Login exitoso sin 2FA
- **WHEN** el usuario envía email y contraseña correctos al endpoint `POST /api/auth/login`
- **THEN** el sistema responde con access token (JWT firmado, expiración 15 minutos) y refresh token (token opaco, expiración 7 días)
- **AND** el access token contiene claims: `sub` (user UUID), `tenant_id` (UUID), `roles` (lista), `type: access`, `iat`, `exp`
- **AND** el access token NO contiene `imp` ni `act` (esos claims solo aparecen en tokens de impersonación)
- **AND** el refresh token se almacena hasheado (SHA-256) en la base de datos con `user_id`, `tenant_id`, `expires_at`, `ip_address`, `user_agent`

#### Scenario: Login con 2FA habilitado gating
- **WHEN** el usuario con `is_2fa_enabled = true` envía email y contraseña correctas
- **THEN** el sistema responde con estado 202 y un `pre_auth_token` temporal (5 minutos)
- **AND** NO emite access ni refresh token hasta que el TOTP sea verificado

### Requirement: Rotación de refresh token
El sistema SHALL invalidar un refresh token inmediatamente después de su uso y emitir un nuevo par access + refresh.

#### Scenario: Refresh exitoso
- **WHEN** el cliente envía un refresh token válido y no usado al endpoint `POST /api/auth/refresh`
- **THEN** el sistema marca el refresh token anterior como `used_at = now()`
- **AND** emite un nuevo access token y un nuevo refresh token
- **AND** el nuevo refresh token se almacena en la base de datos con los mismos metadatos

#### Scenario: Reuse de refresh token
- **WHEN** el cliente envía un refresh token que ya tiene `used_at` seteado
- **THEN** el sistema responde con 401 Unauthorized
- **AND** revoca todos los refresh tokens vigentes del usuario (logout global)
- **AND** registra el evento como intento de reuse en logs de seguridad

#### Scenario: Refresh token expirado
- **WHEN** el cliente envía un refresh token cuya `expires_at` ya pasó
- **THEN** el sistema responde con 401 Unauthorized
- **AND** no emite nuevos tokens

### Requirement: Revocación de sesión (logout)
El sistema SHALL permitir al usuario revocar explícitamente su sesión actual invalidando el refresh token.

#### Scenario: Logout exitoso
- **WHEN** el usuario autenticado envía su refresh token al endpoint `POST /api/auth/logout`
- **THEN** el sistema marca el refresh token como `revoked_at = now()`
- **AND** responde con 204 No Content
- **AND** el access token anterior sigue vigente hasta su expiración natural (15 min máximo)

### Requirement: Resolución de identidad exclusivamente desde JWT verificado
El sistema SHALL derivar `user_id`, `tenant_id` y roles exclusivamente del JWT de access verificado server-side. Cuando el token incluye `imp: true`, `get_current_user` expone el `actor_id` real (claim `act`) y el `impersonated_id` (claim `sub`) mediante un `ImpersonationContext`. Ningún parámetro de la petición puede alterar la identidad.

#### Scenario: Identidad desde access token válido sin impersonación
- **WHEN** un endpoint protegido recibe un access token válido sin claim `imp` en el header `Authorization: Bearer <token>`
- **THEN** la dependencia `get_current_user` resuelve `user_id`, `tenant_id` y `roles` desde los claims verificados
- **AND** `is_impersonating = False` y `actor_id = user_id`
- **AND** cualquier `id` o campo en el body/query se trata como dato de negocio, no como identidad

#### Scenario: Identidad desde access token de impersonación
- **WHEN** un endpoint protegido recibe un access token con `imp: true`, `sub = target_uuid`, `act = actor_uuid`
- **THEN** `get_current_user` resuelve `user_id = target_uuid`, `actor_id = actor_uuid`, `is_impersonating = True`
- **AND** los permisos se evalúan contra los `roles` del target (claim `roles`)
- **AND** las llamadas a `record_audit` usan `actor_id = actor_uuid` e `impersonado_id = target_uuid`

#### Scenario: Access token manipulado
- **WHEN** un cliente envía un access token cuya firma no coincide
- **THEN** el sistema responde con 401 Unauthorized
- **AND** no resuelve identidad ni permite acceso al recurso

#### Scenario: Identidad no alterable por parámetro
- **WHEN** un usuario autenticado envía en el body un campo `user_id` o `tenant_id` distinto al de su sesión
- **THEN** el sistema ignora esos campos para fines de identidad
- **AND** opera con la identidad del JWT verificado

### Requirement: Claims mínimos y permisos fuera del token
El JWT access token SOLO lleva claims mínimos de identidad más los claims opcionales de impersonación. Los permisos se resuelven server-side en cada petición.

#### Scenario: Claims del access token normal
- **WHEN** se decodifica un access token válido sin impersonación
- **THEN** contiene `sub`, `tenant_id`, `roles`, `type: access`, `iat`, `exp`
- **AND** NO contiene permisos finos (`modulo:accion`)
- **AND** NO contiene `imp` ni `act`

#### Scenario: Claims del access token de impersonación
- **WHEN** se decodifica un access token de impersonación
- **THEN** contiene `sub` (target), `act` (actor), `imp: true`, `tenant_id`, `roles`, `type: access`, `iat`, `exp`
- **AND** NO contiene permisos finos (`modulo:accion`)

#### Scenario: Resolución de permisos server-side
- **WHEN** un endpoint declara `require_permission("calificaciones:importar")`
- **THEN** el sistema consulta la base de datos (o caché) para determinar si los roles del usuario otorgan ese permiso
- **AND** la decisión no depende de datos del token más allá de `roles`
