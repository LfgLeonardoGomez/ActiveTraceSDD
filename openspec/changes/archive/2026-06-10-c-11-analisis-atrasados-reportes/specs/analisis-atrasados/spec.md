## ADDED Requirements

### Requirement: Detectar alumnos atrasados por asignación
El sistema SHALL identificar como **atrasado** a todo alumno de una `EntradaPadron` activa que cumpla al menos una de las condiciones de RN-06: tiene actividades sin nota registrada, o tiene `aprobado = False` en al menos una actividad de la asignación. El cómputo DEBE respetar el scope `(asignacion_id)` y el `UmbralMateria` vigente para esa asignación.

#### Scenario: Alumno sin ninguna calificación es atrasado
- **WHEN** un alumno tiene `EntradaPadron` activa en una asignación y no tiene ninguna `Calificacion` registrada
- **THEN** el sistema lo incluye en la lista de atrasados con motivo `sin_datos`

#### Scenario: Alumno con nota inferior al umbral es atrasado
- **WHEN** un alumno tiene `Calificacion.aprobado = False` en al menos una actividad de la asignación
- **THEN** el sistema lo incluye en la lista de atrasados con motivo `nota_insuficiente`

#### Scenario: Alumno con todas las actividades aprobadas no es atrasado
- **WHEN** todas las `Calificacion` del alumno en la asignación tienen `aprobado = True`
- **THEN** el sistema NO lo incluye en la lista de atrasados

#### Scenario: Alumno con actividades faltantes es atrasado
- **WHEN** el alumno no tiene `Calificacion` para una o más actividades incluidas en la asignación
- **THEN** el sistema lo incluye en la lista de atrasados con motivo `actividades_faltantes`

### Requirement: API de consulta de atrasados filtrable
El sistema SHALL exponer `GET /api/analisis/atrasados` que devuelva la lista paginada de alumnos atrasados de una asignación, con los filtros disponibles definidos por el rol del solicitante.

#### Scenario: PROFESOR consulta sus atrasados
- **WHEN** un PROFESOR con permiso `atrasados:ver` llama `GET /api/analisis/atrasados?asignacion_id=<id>`
- **THEN** el sistema devuelve solo los atrasados de esa asignación si el PROFESOR es el titular; de lo contrario devuelve 403

#### Scenario: COORDINADOR consulta atrasados de cualquier materia del tenant
- **WHEN** un COORDINADOR con permiso `atrasados:ver` llama `GET /api/analisis/atrasados?asignacion_id=<id>`
- **THEN** el sistema devuelve los atrasados de cualquier asignación del tenant sin restricción de titularidad

#### Scenario: Paginación obligatoria
- **WHEN** se llama el endpoint sin `page`/`page_size`
- **THEN** el sistema usa `page=1, page_size=50` por defecto y devuelve metadatos `total`, `page`, `pages`

### Requirement: Guard de permiso atrasados:ver
El sistema SHALL exigir el permiso `atrasados:ver` en todos los endpoints del módulo de análisis. Sin permiso explícito → 403.

#### Scenario: Usuario sin permiso
- **WHEN** un usuario sin `atrasados:ver` accede a cualquier endpoint de `/api/analisis/`
- **THEN** el sistema devuelve 403 Forbidden

### Requirement: Aislamiento multi-tenant en análisis
El sistema SHALL filtrar todos los resultados analíticos por `tenant_id` de la sesión activa.

#### Scenario: Tenants aislados
- **WHEN** un usuario del Tenant A consulta atrasados
- **THEN** el sistema devuelve exclusivamente datos del Tenant A, sin posibilidad de acceder a datos del Tenant B
