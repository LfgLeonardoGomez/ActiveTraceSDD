## ADDED Requirements

### Requirement: Crear usuario con PII cifrada
El sistema SHALL crear un usuario dentro del tenant del actor autenticado. Los campos PII (`email`, `dni`, `cuil`, `cbu`, `alias_cbu`) DEBEN almacenarse cifrados con AES-256-GCM en reposo. El campo `email_hash` (HMAC-SHA256 del email normalizado) SHALL almacenarse junto al email cifrado para permitir lookups eficientes. La operación debe fallar con 409 si ya existe un usuario activo con el mismo email en el tenant.

#### Scenario: Creación exitosa de usuario
- **WHEN** un actor con permiso `usuarios:gestionar` envía `POST /api/v1/admin/usuarios` con datos válidos (nombre, apellidos, email, estado)
- **THEN** el sistema crea el usuario con `tenant_id` del JWT, cifra los campos PII, calcula `email_hash`, retorna 201 con el recurso (email desencriptado, DNI/CBU enmascarados)

#### Scenario: Conflicto de email duplicado en el mismo tenant
- **WHEN** un actor con `usuarios:gestionar` intenta crear un usuario con un email que ya existe (activo) en el mismo tenant
- **THEN** el sistema retorna 409 con detalle del conflicto. No se crea ningún registro.

#### Scenario: Email duplicado en tenant diferente es permitido
- **WHEN** el mismo email ya existe en un tenant distinto
- **THEN** el sistema crea el usuario normalmente (409 solo aplica dentro del mismo tenant)

#### Scenario: Actor sin permiso recibe 403
- **WHEN** un actor sin permiso `usuarios:gestionar` intenta crear un usuario
- **THEN** el sistema retorna 403. No se crea ningún registro.

### Requirement: PII nunca expuesta en texto plano en logs ni en responses de listado
Los campos PII del usuario NO DEBEN aparecer en texto plano en logs estructurados, mensajes de error, ni en responses de listado masivo. En el listado: `dni` y `cuil` se devuelven enmascarados (solo últimos 4 caracteres). Los campos `cbu` y `alias_cbu` NO se devuelven en el listado; solo en el detalle individual.

#### Scenario: PII enmascarada en listado
- **WHEN** un actor con `usuarios:gestionar` solicita `GET /api/v1/admin/usuarios`
- **THEN** el response incluye `email` desencriptado, `dni` enmascarado (ej: `****1234`), `cuil` enmascarado, y los campos `cbu`/`alias_cbu` ausentes del response

#### Scenario: PII completa disponible en detalle individual
- **WHEN** un actor con `usuarios:gestionar` solicita `GET /api/v1/admin/usuarios/{id}`
- **THEN** el response incluye todos los campos PII desencriptados (email, dni, cuil, cbu, alias_cbu)

#### Scenario: PII no aparece en logs de error
- **WHEN** ocurre una excepción durante la creación o actualización de un usuario
- **THEN** el log estructurado NO incluye valores en texto plano de campos PII en ningún campo del log

### Requirement: Listar usuarios del tenant con paginación
El sistema SHALL listar los usuarios activos (no soft-deleted) del tenant del actor autenticado con soporte de paginación (`limit`/`offset`) y filtros opcionales por `estado` y búsqueda libre por nombre/apellidos.

#### Scenario: Listado paginado exitoso
- **WHEN** un actor con `usuarios:gestionar` solicita `GET /api/v1/admin/usuarios?limit=20&offset=0`
- **THEN** el sistema retorna `{ items: [...], total: N, limit: 20, offset: 0 }` con usuarios del tenant, PII enmascarada según D-06

#### Scenario: Aislamiento multi-tenant en listado
- **WHEN** un actor del tenant A solicita `GET /api/v1/admin/usuarios`
- **THEN** el response solo incluye usuarios del tenant A; los usuarios del tenant B no aparecen bajo ninguna circunstancia

### Requirement: Actualizar usuario (parcial)
El sistema SHALL permitir actualización parcial de un usuario vía `PUT /api/v1/admin/usuarios/{id}`. Si el campo `email` cambia, SHALL verificar unicidad (409 si ya existe en el tenant), actualizar `email_hash` y re-cifrar el valor. Solo se actualizan los campos presentes en el body.

#### Scenario: Actualización exitosa sin cambio de email
- **WHEN** un actor con `usuarios:gestionar` envía `PUT /api/v1/admin/usuarios/{id}` con cambios en `nombre`, `banco` u otros campos no-PII
- **THEN** el sistema actualiza solo los campos enviados, retorna 200 con el usuario actualizado

#### Scenario: Cambio de email con unicidad respetada
- **WHEN** un actor con `usuarios:gestionar` actualiza el email a uno no existente en el tenant
- **THEN** el sistema re-cifra el email, recalcula `email_hash`, actualiza y retorna 200

#### Scenario: Cambio de email con conflicto
- **WHEN** un actor con `usuarios:gestionar` intenta cambiar el email a uno que ya pertenece a otro usuario activo del mismo tenant
- **THEN** el sistema retorna 409; el usuario no se modifica

### Requirement: Soft delete de usuario
El sistema SHALL implementar soft delete de usuarios (setea `deleted_at`), nunca borrado físico. Un usuario eliminado no aparece en listados ni puede autenticarse.

#### Scenario: Soft delete exitoso
- **WHEN** un actor con `usuarios:gestionar` envía `DELETE /api/v1/admin/usuarios/{id}`
- **THEN** el sistema setea `deleted_at` en el usuario, retorna 204. El usuario no aparece en listados posteriores.

#### Scenario: Usuario eliminado libera el email para reutilización
- **WHEN** un usuario es soft-deleted y se intenta crear otro usuario con el mismo email en el mismo tenant
- **THEN** el sistema permite la creación (el índice único parcial `WHERE deleted_at IS NULL` no lo bloquea)

### Requirement: Unicidad email por tenant enforced en dos capas
La unicidad `(tenant_id, email)` SHALL ser enforced en la capa de service (409 semántico antes de insertar) y respaldada por un índice único parcial de PostgreSQL sobre `(tenant_id, email_hash) WHERE deleted_at IS NULL` como safety net.

#### Scenario: Índice de DB rechaza violación concurrente
- **WHEN** dos requests concurrentes intentan crear usuarios con el mismo email en el mismo tenant simultáneamente
- **THEN** solo uno tiene éxito; el otro recibe un error (el índice de DB actúa como safety net)
