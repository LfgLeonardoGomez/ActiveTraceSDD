## ADDED Requirements

### Requirement: Enroll de 2FA TOTP
El sistema SHALL permitir a un usuario opt-in habilitar 2FA TOTP, generando un secreto, mostrándolo como QR y validando el primer código antes de activar el flag.

#### Scenario: Generación de secreto y QR
- **WHEN** el usuario autenticado solicita habilitar 2FA al endpoint `POST /api/auth/2fa/enroll`
- **THEN** el sistema genera un secreto TOTP único via `pyotp.random_base32()`
- **AND** cifra el secreto con AES-256 y lo almacena en `two_factor_enrollments` asociado al usuario
- **AND** retorna un provisioning URI (`otpauth://...`) y un QR code (base64 PNG) para que el usuario escanee con su app autenticadora
- **AND** el estado del enroll queda como `pending` hasta confirmación

#### Scenario: Confirmación de enroll con código válido
- **WHEN** el usuario envía el código TOTP generado por su app al endpoint `POST /api/auth/2fa/enroll/confirm`
- **AND** el código es válido contra el secreto almacenado
- **THEN** el sistema activa `is_2fa_enabled = true` en el usuario
- **AND** marca el enroll como `confirmed`
- **AND** retorna códigos de recuperación (backup codes) de un solo uso (10 códigos de 8 caracteres alfanuméricos)
- **AND** almacena los hashes de los códigos de recuperación para validación futura

#### Scenario: Confirmación de enroll con código inválido
- **WHEN** el usuario envía un código TOTP incorrecto
- **THEN** el sistema responde con 400 Bad Request
- **AND** no activa `is_2fa_enabled`
- **AND** conserva el enroll en estado `pending` permitiendo reintentos

### Requirement: Verificación de TOTP en login
El sistema SHALL exigir el código TOTP después de validar credenciales si el usuario tiene `is_2fa_enabled = true`.

#### Scenario: Login con 2FA — verificación exitosa
- **WHEN** el usuario con 2FA habilitado envía email + password correctos
- **THEN** el sistema responde con 202 y un `pre_auth_token` (JWT de corta vida, 5 min, claim `type: pre_auth`)
- **AND** el usuario envía el `pre_auth_token` + código TOTP a `POST /api/auth/2fa/verify`
- **AND** el código es válido
- **THEN** el sistema emite el par access + refresh token normal

#### Scenario: Login con 2FA — verificación fallida
- **WHEN** el usuario con 2FA habilitado envía email + password correctos
- **THEN** recibe el `pre_auth_token`
- **AND** envía un código TOTP inválido
- **THEN** el sistema responde con 401 Unauthorized
- **AND** no emite access ni refresh token
- **AND** decrementa un contador de reintentos; tras 5 fallos consecutivos invalida el `pre_auth_token`

#### Scenario: Login sin 2FA habilitado no exige TOTP
- **WHEN** el usuario con `is_2fa_enabled = false` envía credenciales válidas
- **THEN** el sistema emite access + refresh token directamente sin paso intermedio

### Requirement: Deshabilitación de 2FA
El sistema SHALL permitir al usuario deshabilitar 2FA previa verificación de un código TOTP válido.

#### Scenario: Deshabilitar 2FA
- **WHEN** el usuario autenticado solicita deshabilitar 2FA con un código TOTP válido
- **THEN** el sistema setea `is_2fa_enabled = false`
- **AND** soft-deletea el registro de `two_factor_enrollments` del usuario (marcado `deleted_at`)
- **AND** invalida todos los códigos de recuperación asociados

### Requirement: Uso de códigos de recuperación
El sistema SHALL permitir al usuario con 2FA habilitado autenticarse usando un código de recuperación si perdió acceso a su app TOTP.

#### Scenario: Recuperación con backup code
- **WHEN** el usuario envía un código de recuperación válido en lugar del TOTP
- **THEN** el sistema valida el hash del código contra los almacenados
- **AND** marca ese código como usado (soft-delete del registro o `used_at`)
- **AND** emite access + refresh token
- **AND** alerta al usuario de que debe re-enrollar 2FA (opcional, para MVP se loggea)

#### Scenario: Código de recuperación ya usado
- **WHEN** el usuario envía un código de recuperación que ya tiene `used_at`
- **THEN** el sistema responde con 401 Unauthorized
- **AND** trata el intento como login fallido para fines de rate limiting
