## ADDED Requirements

### Requirement: Modelo AuditLog append-only con campos de trazabilidad completa
El sistema SHALL persistir un registro `AuditLog` por cada acción significativa, con los campos `id`, `tenant_id`, `fecha_hora`, `actor_id`, `impersonado_id`, `materia_id`, `accion`, `detalle`, `filas_afectadas`, `ip`, `user_agent`. El modelo NO tiene `updated_at`, `deleted_at` ni ningún campo mutable post-inserción. No hereda `SoftDeleteMixin`.

#### Scenario: Inserción de un registro de auditoría
- **WHEN** se llama a `audit_log_repository.insert(entry)` con todos los campos requeridos
- **THEN** el registro queda persistido en la tabla `audit_log` con `fecha_hora` en UTC
- **AND** el registro tiene un `id` UUID generado por la base de datos

#### Scenario: Campos nullable opcionales
- **WHEN** se inserta un `AuditLog` sin `impersonado_id`, `materia_id` o `detalle`
- **THEN** esos campos se almacenan como NULL sin error

### Requirement: Restricción append-only a nivel de base de datos
La tabla `audit_log` SHALL tener un trigger BEFORE UPDATE OR DELETE que lanza una excepción. Ningún UPDATE ni DELETE puede ejecutarse sobre la tabla, independientemente de la capa que lo intente.

#### Scenario: Intento de UPDATE rechazado por el trigger
- **WHEN** se ejecuta `UPDATE audit_log SET accion = 'X' WHERE id = '<uuid>'`
- **THEN** la base de datos lanza una excepción con mensaje que incluye "audit_log is immutable"
- **AND** el registro original no es modificado

#### Scenario: Intento de DELETE rechazado por el trigger
- **WHEN** se ejecuta `DELETE FROM audit_log WHERE id = '<uuid>'`
- **THEN** la base de datos lanza una excepción con mensaje que incluye "audit_log is immutable"
- **AND** el registro original permanece en la tabla

#### Scenario: INSERT sigue funcionando tras el trigger
- **WHEN** se inserta un nuevo registro en `audit_log` después de que el trigger está instalado
- **THEN** la inserción se completa con éxito sin activar el trigger

### Requirement: Migración 004 crea la tabla y el trigger
La migración 004 SHALL crear la tabla `audit_log`, la función `deny_audit_log_mutation`, y el trigger `trg_audit_log_immutable`. El rollback SHALL eliminar el trigger, la función y la tabla en ese orden.

#### Scenario: Migración aplicada desde cero
- **WHEN** se ejecuta `alembic upgrade head` en una DB vacía (o tras 003)
- **THEN** la tabla `audit_log` existe con todos sus campos
- **AND** el trigger `trg_audit_log_immutable` está activo en la tabla

#### Scenario: Rollback de la migración
- **WHEN** se ejecuta `alembic downgrade` a la revisión 003
- **THEN** el trigger, la función y la tabla `audit_log` son eliminados sin error

### Requirement: Aislamiento multi-tenant en queries de auditoría
El repositorio de AuditLog SHALL filtrar por `tenant_id` en todos los métodos de lectura. No puede retornar registros de otros tenants.

#### Scenario: Query de auditoría scoped a tenant
- **WHEN** se consultan registros de `audit_log` para `tenant_id = T1`
- **THEN** solo se retornan registros cuyo `tenant_id = T1`
- **AND** registros de otros tenants no aparecen en el resultado
