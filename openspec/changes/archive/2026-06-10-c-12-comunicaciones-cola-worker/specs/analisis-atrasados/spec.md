## MODIFIED Requirements

### Requirement: API de consulta de atrasados filtrable
El sistema SHALL exponer `GET /api/analisis/atrasados` que devuelva la lista paginada de alumnos atrasados de una asignación, con los filtros disponibles definidos por el rol del solicitante. La respuesta SHALL incluir `alumno_email` descifrado para permitir que el frontend popule destinatarios de comunicaciones.

#### Scenario: PROFESOR consulta sus atrasados
- **WHEN** un PROFESOR con permiso `atrasados:ver` llama `GET /api/analisis/atrasados?asignacion_id=<id>`
- **THEN** el sistema devuelve solo los atrasados de esa asignación si el PROFESOR es el titular; de lo contrario devuelve 403

#### Scenario: COORDINADOR consulta atrasados de cualquier materia del tenant
- **WHEN** un COORDINADOR con permiso `atrasados:ver` llama `GET /api/analisis/atrasados?asignacion_id=<id>`
- **THEN** el sistema devuelve los atrasados de cualquier asignación del tenant sin restricción de titularidad

#### Scenario: alumno_email incluido en la respuesta
- **WHEN** se consulta la lista de atrasados
- **THEN** cada item incluye `alumno_email` con el email descifrado del alumno (necesario para poblar destinatarios al encolar comunicaciones)

#### Scenario: Paginación obligatoria
- **WHEN** se llama el endpoint sin `page`/`page_size`
- **THEN** el sistema usa `page=1, page_size=50` por defecto y devuelve metadatos `total`, `page`, `pages`
