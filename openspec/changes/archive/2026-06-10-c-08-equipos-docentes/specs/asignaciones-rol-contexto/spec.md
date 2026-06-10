# Delta for asignaciones-rol-contexto

## MODIFIED Requirements

### Requirement: Endpoints de asignaciones y equipos coexisten
El sistema SHALL mantener los endpoints existentes de `/api/v1/asignaciones` para operaciones CRUD individuales de asignaciones (crear, listar, obtener, actualizar, soft delete). El sistema SHALL agregar nuevos endpoints bajo `/api/v1/equipos/` para operaciones orientadas a equipo (mis-equipos, asignación masiva, clonación, batch vigencia, export). Ambos routers operan sobre la misma tabla `asignaciones` pero con semántica distinta: `/api/v1/asignaciones` es para CRUD de filas individuales; `/api/v1/equipos` es para operaciones de equipo (agregación de múltiples asignaciones en un contexto académico).
(Previously: El router `/api/v1/asignaciones` era el único punto de acceso para toda la gestión de asignaciones. No existía un namespace separado para operaciones de equipo.)

#### Scenario: CRUD de asignación sigue funcionando en asignaciones
- GIVEN una asignación existente
- WHEN un COORDINADOR envía `GET /api/v1/asignaciones/{id}`
- THEN el sistema retorna la asignación individual correctamente

#### Scenario: Operación de equipo se ejecuta en nuevo namespace
- GIVEN el mismo equipo de asignaciones
- WHEN un COORDINADOR envía `GET /api/v1/equipos/equipo?materia_id=X&carrera_id=Y&cohorte_id=Z`
- THEN el sistema retorna el equipo completo con todas las asignaciones del contexto

#### Scenario: Router asignaciones sin equipo filter (comportamiento existente)
- GIVEN el listado de asignaciones
- WHEN un COORDINADOR envía `GET /api/v1/asignaciones` sin parámetros de equipo
- THEN el sistema retorna el listado paginado normal sin agrupación
