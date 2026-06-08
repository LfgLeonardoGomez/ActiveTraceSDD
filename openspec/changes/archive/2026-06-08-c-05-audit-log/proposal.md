## Why

El sistema necesita trazabilidad total desde el primer día: toda acción significativa debe quedar registrada de forma inmutable con actor, tenant, IP y contexto. Además, la funcionalidad de impersonación (soporte/ADMIN operando en nombre de otro usuario) requiere una sesión distinguible y un trail de auditoría propio. Sin este change, C-15, C-19 y cualquier módulo que requiera "quién hizo qué y cuándo" no tienen cimiento.

## What Changes

- Modelo `AuditLog` (E-AUD): tabla append-only con restricciones a nivel DB que bloquean UPDATE y DELETE.
- Campos: `actor_id`, `impersonado_id`, `materia_id`, `accion`, `detalle` (JSONB), `filas_afectadas`, `ip`, `user_agent`, `fecha_hora`, `tenant_id`.
- Migración 004: `audit_log` con regla/trigger DB que rechaza UPDATE y DELETE.
- Helper `audit_action` (función o decorador async) para registrar acciones con código estandarizado.
- Catálogo inicial de códigos de acción: `CALIFICACIONES_IMPORTAR`, `PADRON_CARGAR`, `COMUNICACION_ENVIAR`, `ASIGNACION_MODIFICAR`, `LIQUIDACION_CERRAR`, `IMPERSONACION_INICIAR`, `IMPERSONACION_FINALIZAR`.
- Endpoint `POST /api/auth/impersonate` y `DELETE /api/auth/impersonate`: inicia/finaliza sesión de impersonación; requiere permiso `impersonacion:usar`.
- El JWT de impersonación porta un claim distinguible (`imp: true`, `act: <actor_id>`); el `current_user` dependency resuelve correctamente ambos valores.
- Toda acción bajo impersonación queda atribuida al actor real, no al impersonado.

## Capabilities

### New Capabilities

- `audit-log-model`: Modelo `AuditLog` (E-AUD), migración 004, restricción append-only a nivel DB (regla PostgreSQL que rechaza UPDATE y DELETE sobre la tabla).
- `audit-action-helper`: Función async `record_audit(session, actor_id, tenant_id, accion, ...)` y catálogo de códigos de acción estándar (`AuditAction` enum). Integración con el contexto de request (IP, user_agent).
- `impersonation`: Endpoints `POST/DELETE /api/auth/impersonate`, claim `imp`/`act` en JWT, resolución de identidad real/impersonada en `get_current_user`, registro `IMPERSONACION_INICIAR`/`IMPERSONACION_FINALIZAR` en audit log.

### Modified Capabilities

- `jwt-auth`: El `get_current_user` dependency debe leer el claim `imp` para exponer el actor real cuando hay impersonación activa. El contrato del token cambia: se agrega campo `imp: bool` y `act: UUID` opcionales.

## Impact

- **Backend**: `backend/app/models/audit_log.py`, `backend/app/repositories/audit_log_repository.py`, `backend/app/services/audit_service.py`, `backend/app/core/audit.py` (helper), `backend/app/api/v1/routers/auth.py` (impersonate endpoints), `backend/app/core/dependencies.py` (get_current_user + ImpersonationContext).
- **Migraciones**: `backend/alembic/versions/004_audit_log.py`.
- **Tests**: append-only (UPDATE/DELETE rechazados a nivel DB y servicio), atribución bajo impersonación, registro de acción con código + filas afectadas, isolación multi-tenant.
- **Dependencias externas**: ninguna.
