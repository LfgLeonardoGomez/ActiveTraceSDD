## ADDED Requirements

### Requirement: Solicitud de recuperación de contraseña
El sistema SHALL generar un token criptográfico de un solo uso y corta expiración cuando un usuario solicita recuperar su contraseña indicando su email.

#### Scenario: Solicitud con email existente
- **WHEN** el usuario anónimo envía `POST /api/auth/forgot` con un email registrado en el tenant
- **THEN** el sistema genera un token aleatorio de 32 bytes (`secrets.token_urlsafe()`)
- **AND** almacena su hash (SHA-256) en `password_reset_tokens` con `user_id`, `tenant_id`, `expires_at` (1 hora desde creación), `created_at`, `used_at = null`
- **AND** retorna 202 Accepted (sin exponer si el email existe en el body, pero el comportamiento de tiempo es idéntico para email inexistente para evitar enumeración)

#### Scenario: Solicitud con email inexistente
- **WHEN** el usuario anónimo envía un email no registrado
- **THEN** el sistema ejecuta el mismo procesamiento (delay constante) sin generar token
- **AND** retorna 202 Accepted
- **AND** no expone diferencia respecto al escenario de email existente

#### Scenario: Múltiples solicitudes consecutivas
- **WHEN** el usuario solicita recuperación y ya tiene un token vigente sin usar
- **THEN** el sistema puede invalidar el token anterior y generar uno nuevo (opcional, configurable por tenant)
- **AND** en MVP simplemente permite coexistencia; el primero en ser usado invalida al resto del mismo usuario al resetear la contraseña

### Requirement: Restablecimiento de contraseña
El sistema SHALL permitir al usuario establecer una nueva contraseña consumiendo un token de recuperación válido.

#### Scenario: Reset con token válido
- **WHEN** el usuario envía `POST /api/auth/reset` con token válido, no usado, no expirado, y nueva contraseña (cumpliendo política de complejidad)
- **THEN** el sistema actualiza el `password_hash` del usuario con Argon2id
- **AND** marca el token como `used_at = now()`
- **AND** invalida todos los refresh tokens vigentes del usuario (logout global)
- **AND** responde con 204 No Content

#### Scenario: Reset con token expirado
- **WHEN** el usuario envía un token cuya `expires_at` ya pasó
- **THEN** el sistema responde con 400 Bad Request
- **AND** no modifica la contraseña
- **AND** el token permanece sin `used_at` (no se consume)

#### Scenario: Reset con token ya usado
- **WHEN** el usuario envía un token que ya tiene `used_at` seteado
- **THEN** el sistema responde con 400 Bad Request
- **AND** no modifica la contraseña
- **AND** registra el intento en logs de seguridad

#### Scenario: Reset con contraseña débil
- **WHEN** el usuario envía una nueva contraseña que no cumple la política (mínimo 8 caracteres, 1 mayúscula, 1 minúscula, 1 número)
- **THEN** el sistema responde con 422 Unprocessable Entity
- **AND** no modifica la contraseña
- **AND** el token permanece válido para reintentar

### Requirement: Single-use del token de recuperación
El token de recuperación SOLO puede usarse una vez. Su consumo es atómico y definitivo.

#### Scenario: Consumo atómico
- **WHEN** dos requests concurrentes llegan con el mismo token válido
- **THEN** una sola request tiene éxito (race condition resuelta por transacción o constraint único en `used_at`)
- **AND** la segunda request recibe 400 Bad Request
