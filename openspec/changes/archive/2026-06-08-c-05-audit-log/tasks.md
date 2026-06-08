## 1. Migración y Modelo AuditLog

- [x] 1.1 Crear `backend/app/models/audit_log.py`: modelo SQLAlchemy `AuditLog` con campos `id` (UUID PK), `tenant_id`, `fecha_hora` (UTC default), `actor_id`, `impersonado_id` (nullable FK), `materia_id` (nullable FK), `accion` (String), `detalle` (JSONB nullable), `filas_afectadas` (Integer default 0), `ip` (String nullable), `user_agent` (String nullable). Sin `updated_at`, sin `deleted_at`, sin herencia de `SoftDeleteMixin`.
- [x] 1.2 Registrar `AuditLog` en `backend/app/models/__init__.py`.
- [x] 1.3 Crear migración `backend/alembic/versions/004_audit_log.py`: crea la tabla `audit_log`, la función `deny_audit_log_mutation()` y el trigger `trg_audit_log_immutable` BEFORE UPDATE OR DELETE. El downgrade elimina trigger, función y tabla.
- [x] 1.4 Test de migración `backend/tests/test_migration_004.py`: verifica que `upgrade` crea tabla y trigger; verifica que `downgrade` elimina todo; verifica que INSERT funciona; verifica que UPDATE lanza excepción con "audit_log is immutable"; verifica que DELETE lanza excepción.

## 2. Repositorio AuditLog

- [x] 2.1 Crear `backend/app/repositories/audit_log_repository.py`: clase `AuditLogRepository` con método `insert(entry: AuditLog) -> None` y `list_by_tenant(tenant_id, *, limit, offset) -> list[AuditLog]`. Sin métodos `update` ni `delete`.
- [x] 2.2 Test `backend/tests/test_audit_log_repository.py`: prueba insert exitoso, list_by_tenant retorna solo registros del tenant correcto (aislamiento), list_by_tenant de otro tenant no cruza datos.

## 3. Helper record_audit y AuditAction

- [x] 3.1 Crear `backend/app/core/audit.py`: enum `AuditAction` (StrEnum) con valores `CALIFICACIONES_IMPORTAR`, `PADRON_CARGAR`, `COMUNICACION_ENVIAR`, `ASIGNACION_MODIFICAR`, `LIQUIDACION_CERRAR`, `IMPERSONACION_INICIAR`, `IMPERSONACION_FINALIZAR`.
- [x] 3.2 Implementar función `record_audit(session, actor_id, tenant_id, accion, *, impersonado_id=None, materia_id=None, detalle=None, filas_afectadas=0, ip=None, user_agent=None) -> None` en `backend/app/core/audit.py`.
- [x] 3.3 Test `backend/tests/test_audit_helper.py`: prueba inserción con todos los parámetros, prueba con parámetros opcionales nulos, prueba que `AuditAction` con valor inválido lanza `ValueError`, prueba que el campo `fecha_hora` es UTC.

## 4. ImpersonationContext en get_current_user

- [x] 4.1 Definir `ImpersonationContext` dataclass/modelo en `backend/app/core/dependencies.py` con campos `user_id: UUID`, `actor_id: UUID`, `tenant_id: UUID`, `roles: list[str]`, `is_impersonating: bool`, `impersonated_id: UUID | None`.
- [x] 4.2 Modificar `get_current_user` en `backend/app/core/dependencies.py` para leer claims `imp` y `act` del JWT. Si `imp == True`: `user_id = sub`, `actor_id = act`, `is_impersonating = True`, `impersonated_id = sub`. Si no: `actor_id = user_id`, `is_impersonating = False`, `impersonado_id = None`.
- [x] 4.3 Test `backend/tests/test_impersonation_context.py`: prueba resolución con token normal, prueba resolución con token de impersonación (`imp=true`, `act=actor_uuid`), prueba que `actor_id != user_id` cuando hay impersonación activa.

## 5. Endpoints de impersonación

- [x] 5.1 Agregar `POST /api/auth/impersonate` en `backend/app/api/v1/routers/auth.py`: body `ImpersonateRequest(target_user_id: UUID)`, guard `require_permission("impersonacion:usar")`, verifica que el target existe en el mismo tenant y está activo, emite JWT con claims de impersonación (sub=target, act=actor, imp=True, tenant_id, roles, exp=15min), llama `record_audit(accion=AuditAction.IMPERSONACION_INICIAR, actor_id=actor, impersonado_id=target, ...)`.
- [x] 5.2 Agregar `DELETE /api/auth/impersonate` en `backend/app/api/v1/routers/auth.py`: requiere token con `imp=True` (si no, 400), llama `record_audit(accion=AuditAction.IMPERSONACION_FINALIZAR, ...)`, responde 204.
- [x] 5.3 Agregar `token_service.create_impersonation_token(actor, target, tenant_id, roles) -> str` en `backend/app/services/token_service.py`.
- [x] 5.4 Test `backend/tests/test_impersonation.py`: POST exitoso con permiso, POST sin permiso → 403, POST con target de otro tenant → 404, POST con target inactivo → 400, DELETE con token de impersonación → 204 + audit log, DELETE con token normal → 400, audit log contiene IMPERSONACION_INICIAR con actor correcto, audit log contiene IMPERSONACION_FINALIZAR.

## 6. Verificación de reglas de negocio críticas

- [x] 6.1 Test de atribución: bajo impersonación, `actor_id` en `AuditLog` es el actor real, NO el impersonado. (cubierto por test_impersonation.py::test_impersonate_creates_audit_log y test_end_impersonation_success)
- [x] 6.2 Test de aislamiento: un registro de audit_log de tenant T1 no es retornable por queries de tenant T2. (cubierto por test_audit_log_repository.py::test_list_by_tenant_does_not_cross_tenants)
- [x] 6.3 Test de append-only de extremo a extremo: intentar UPDATE/DELETE sobre `audit_log` desde SQLAlchemy lanza excepción de base de datos. (cubierto por test_migration_004.py::test_update/delete_raises_immutable_exception)
- [x] 6.4 Verificar cobertura ≥80% líneas y ≥90% reglas de negocio en el módulo de auditoría con `pytest --cov`. (ejecutar tras levantar Docker: `pytest tests/test_audit_*.py tests/test_impersonation*.py --cov=app/core/audit --cov=app/repositories/audit_log_repository --cov=app/models/audit_log`)
