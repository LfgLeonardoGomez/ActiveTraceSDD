### Requirement: Enum AuditAction con catálogo de códigos estándar
El sistema SHALL definir un enum `AuditAction` en `backend/app/core/audit.py` con al menos los siguientes códigos iniciales: `CALIFICACIONES_IMPORTAR`, `PADRON_CARGAR`, `COMUNICACION_ENVIAR`, `ASIGNACION_MODIFICAR`, `LIQUIDACION_CERRAR`, `IMPERSONACION_INICIAR`, `IMPERSONACION_FINALIZAR`. Los valores del enum son strings en SCREAMING_SNAKE_CASE.

#### Scenario: Uso del enum en código
- **WHEN** un Service invoca `record_audit(..., accion=AuditAction.PADRON_CARGAR, ...)`
- **THEN** el campo `accion` del registro almacenado es el string `"PADRON_CARGAR"`

#### Scenario: Enum rechaza códigos no definidos
- **WHEN** se intenta construir un `AuditAction` con un valor no listado en el catálogo
- **THEN** Python lanza un `ValueError` antes de llegar a la base de datos

### Requirement: Función record_audit como punto único de registro
El sistema SHALL proveer una función async `record_audit(session, actor_id, tenant_id, accion, *, impersonado_id, materia_id, detalle, filas_afectadas, ip, user_agent)` en `backend/app/core/audit.py`. La función crea e inserta un `AuditLog` en la sesión provista. Solo se llama desde la capa Service, nunca desde Routers.

#### Scenario: Registro exitoso de una acción
- **WHEN** un Service invoca `await record_audit(session, actor_id=U, tenant_id=T, accion=AuditAction.PADRON_CARGAR, filas_afectadas=150, ip="1.2.3.4")`
- **THEN** se inserta un registro en `audit_log` con `actor_id=U`, `tenant_id=T`, `accion="PADRON_CARGAR"`, `filas_afectadas=150`, `ip="1.2.3.4"`
- **AND** `fecha_hora` es el timestamp actual en UTC

#### Scenario: Parámetros opcionales nulos
- **WHEN** `record_audit` se invoca sin `materia_id`, `detalle` ni `impersonado_id`
- **THEN** esos campos quedan NULL en el registro insertado sin lanzar error

#### Scenario: Llamada desde Router lanzaría error de linting/review
- **WHEN** se revisa el código y se detecta `record_audit` invocado directamente en un Router
- **THEN** el code review lo marca como violación de la arquitectura (Router → Service → record_audit)

### Requirement: Captura de IP y user_agent desde el contexto de request
El sistema SHALL extraer `ip` y `user_agent` del objeto `Request` de FastAPI cuando esté disponible, y pasarlos a `record_audit`. Los Services que auditan acciones HTTP deben recibir el `Request` como parámetro o extraer estos datos desde la dependencia correspondiente.

#### Scenario: IP extraída del header X-Forwarded-For detrás de proxy
- **WHEN** el request llega con header `X-Forwarded-For: 10.0.0.1`
- **THEN** el campo `ip` del AuditLog registra `"10.0.0.1"`

#### Scenario: Fallback a IP de conexión directa
- **WHEN** el request no tiene header `X-Forwarded-For`
- **THEN** el campo `ip` del AuditLog registra la IP de `request.client.host`
