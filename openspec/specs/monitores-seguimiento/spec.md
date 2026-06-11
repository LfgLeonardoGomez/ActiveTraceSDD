## ADDED Requirements

### Requirement: Monitor general de actividades (coordinación/admin)
El sistema SHALL exponer `GET /api/analisis/monitor/general` accesible para COORDINADOR y ADMIN con permiso `atrasados:ver`. Devuelve una vista paginada transversal de todos los alumnos del tenant con su estado de actividades.

#### Scenario: COORDINADOR visualiza monitor general
- **WHEN** un COORDINADOR con `atrasados:ver` llama `GET /api/analisis/monitor/general`
- **THEN** el sistema devuelve todos los alumnos del tenant (de todas las materias y asignaciones) paginados con su estado de actividades

#### Scenario: Filtros disponibles en monitor general
- **WHEN** el COORDINADOR aplica filtros `materia_id`, `regional`, `comision`, `alumno` (búsqueda libre), `estado_actividad` (`atrasado` | `al_dia` | `sin_datos`) y `criterio_clasificacion`
- **THEN** el sistema devuelve únicamente los registros que satisfacen todos los filtros activos

#### Scenario: PROFESOR no puede acceder al monitor general
- **WHEN** un PROFESOR intenta acceder a `GET /api/analisis/monitor/general`
- **THEN** el sistema devuelve 403 Forbidden (scope `is_propio` impide acceso al monitor global)

### Requirement: Export CSV del monitor general
El sistema SHALL permitir descargar los resultados del monitor general (con los filtros activos) como CSV mediante `GET /api/analisis/monitor/general/export`.

#### Scenario: Export respeta los filtros activos
- **WHEN** el COORDINADOR llama al export con `materia_id=X` aplicado
- **THEN** el CSV contiene solo los alumnos de esa materia, con columnas `alumno, email, materia, actividades_aprobadas, actividades_totales, estado`

#### Scenario: Export sin filtros exporta todo el tenant
- **WHEN** el COORDINADOR llama al export sin filtros
- **THEN** el CSV incluye todos los alumnos del tenant (sin límite de paginación en el export)

### Requirement: Monitor de seguimiento (vista tutor/profesor)
El sistema SHALL exponer `GET /api/analisis/monitor/propio` accesible para TUTOR y PROFESOR con `atrasados:ver`. Devuelve únicamente los alumnos de las asignaciones activas del usuario autenticado.

#### Scenario: TUTOR ve solo sus alumnos asignados
- **WHEN** un TUTOR llama `GET /api/analisis/monitor/propio`
- **THEN** el sistema devuelve solo los alumnos de las asignaciones donde el TUTOR es titular

#### Scenario: Filtros del monitor propio
- **WHEN** el TUTOR aplica filtros `alumno`, `email`, `comision`, `regional`, `actividad_id` y `min_actividades_cumplidas`
- **THEN** el sistema devuelve únicamente los registros que satisfacen todos los filtros activos

#### Scenario: PROFESOR ve solo sus propias asignaciones
- **WHEN** un PROFESOR con `atrasados:ver` llama `GET /api/analisis/monitor/propio`
- **THEN** el sistema devuelve los alumnos de sus asignaciones activas, no los de otros docentes en las mismas materias

### Requirement: Monitor de seguimiento extendido (vista coordinación/admin)
El sistema SHALL exponer `GET /api/analisis/monitor/global` para COORDINADOR y ADMIN que extiende el monitor propio con un filtro adicional de rango de fechas (`fecha_desde`, `fecha_hasta`) para acotar el período de análisis (F2.9).

#### Scenario: Filtro por rango de fechas acota los datos analizados
- **WHEN** un COORDINADOR consulta con `fecha_desde=2025-03-01&fecha_hasta=2025-06-30`
- **THEN** el sistema considera solo las `Calificacion` cuyo `created_at` cae en ese rango para el cómputo de aprobados y atrasados

#### Scenario: Sin rango de fechas analiza todos los datos
- **WHEN** el COORDINADOR llama sin `fecha_desde` ni `fecha_hasta`
- **THEN** el sistema devuelve el estado actual sin restricción temporal (equivalente a F2.8)

### Requirement: Paginación en todos los monitores
Los monitores SHALL paginar los resultados con un máximo de 100 registros por página por defecto. El parámetro `page_size` DEBE estar disponible con un máximo de 100.

#### Scenario: Paginación por defecto
- **WHEN** se llama cualquier monitor sin parámetros de paginación
- **THEN** el sistema usa `page=1, page_size=50` y devuelve metadatos `total`, `page`, `pages`

#### Scenario: page_size mayor al máximo rechazado
- **WHEN** se solicita `page_size=200`
- **THEN** el sistema devuelve 422 indicando que el máximo permitido es 100
