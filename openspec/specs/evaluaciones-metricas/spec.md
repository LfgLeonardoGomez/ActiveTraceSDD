## ADDED Requirements

### Requirement: Panel de métricas globales de coloquios
El sistema SHALL exponer `GET /api/coloquios/metricas` devolviendo métricas agregadas de todas las convocatorias activas del tenant: total de alumnos cargados, cantidad de instancias activas, reservas activas y notas registradas.

#### Scenario: COORDINADOR consulta métricas globales
- **WHEN** un COORDINADOR con `coloquios:ver` llama `GET /api/coloquios/metricas`
- **THEN** el sistema devuelve `total_alumnos_cargados`, `instancias_activas`, `reservas_activas` y `notas_registradas` para todo el tenant

#### Scenario: Aislamiento multi-tenant en métricas
- **WHEN** se consultan las métricas globales
- **THEN** el sistema agrega exclusivamente datos del tenant de la sesión activa, sin cruzar datos de otros tenants

#### Scenario: Sin permiso coloquios:ver
- **WHEN** un usuario sin `coloquios:ver` accede a las métricas
- **THEN** el sistema devuelve 403 Forbidden

### Requirement: Agenda consolidada de reservas activas (coordinación)
El sistema SHALL exponer `GET /api/coloquios/agenda` devolviendo la lista paginada de todas las reservas activas de todas las convocatorias del tenant, filtrable por `evaluacion_id`, `fecha_desde`, `fecha_hasta` y `materia_id`. Solo accesible para COORDINADOR y ADMIN.

#### Scenario: COORDINADOR consulta agenda global
- **WHEN** un COORDINADOR con `coloquios:gestionar` llama `GET /api/coloquios/agenda`
- **THEN** el sistema devuelve todas las reservas activas del tenant con alumno_nombre, convocatoria, materia y fecha_hora

#### Scenario: Filtro por materia
- **WHEN** se llama `GET /api/coloquios/agenda?materia_id=<id>`
- **THEN** el sistema devuelve solo las reservas activas de convocatorias de esa materia

#### Scenario: Filtro por rango de fechas
- **WHEN** se llama `GET /api/coloquios/agenda?fecha_desde=2026-06-01&fecha_hasta=2026-06-30`
- **THEN** el sistema devuelve solo las reservas cuya `fecha_hora` cae dentro del rango

#### Scenario: PROFESOR no puede ver la agenda global
- **WHEN** un PROFESOR intenta acceder a `GET /api/coloquios/agenda`
- **THEN** el sistema devuelve 403 Forbidden

### Requirement: Guard de permisos de coloquios
El sistema SHALL exigir el permiso correspondiente en cada endpoint del módulo de coloquios. Sin permiso explícito → 403.

#### Scenario: Usuario sin ningún permiso de coloquios
- **WHEN** un usuario sin `coloquios:gestionar`, `coloquios:reservar` ni `coloquios:ver` accede a cualquier endpoint de `/api/coloquios/`
- **THEN** el sistema devuelve 403 Forbidden
