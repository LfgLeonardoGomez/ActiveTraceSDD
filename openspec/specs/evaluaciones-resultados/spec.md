## ADDED Requirements

### Requirement: Registrar resultado de evaluación por alumno
El sistema SHALL permitir registrar o actualizar el resultado final de un alumno en una convocatoria vía `POST /api/coloquios/{id}/resultados`. El resultado es texto libre (numérico o cualitativo). No se deriva `aprobado` automáticamente.

#### Scenario: Registrar resultado nuevo
- **WHEN** un COORDINADOR o ADMIN con `coloquios:gestionar` envía `POST /api/coloquios/{id}/resultados` con alumno_id y nota_final
- **THEN** el sistema crea o actualiza el `ResultadoEvaluacion` para ese alumno y devuelve 200

#### Scenario: Actualizar resultado existente (upsert)
- **WHEN** ya existe un `ResultadoEvaluacion` para el mismo `(evaluacion_id, alumno_id)` y se registra nuevamente
- **THEN** el sistema actualiza la `nota_final` existente (upsert, no duplica el registro)

#### Scenario: Alumno no está en el padrón de candidatos
- **WHEN** se intenta registrar un resultado para un alumno que no está en `evaluacion_candidato` de la convocatoria
- **THEN** el sistema devuelve 404 (el alumno no pertenece a esa convocatoria)

#### Scenario: Sin permiso para registrar resultados
- **WHEN** un PROFESOR o TUTOR intenta registrar un resultado
- **THEN** el sistema devuelve 403 Forbidden

### Requirement: Consultar registro académico consolidado de una convocatoria
El sistema SHALL exponer `GET /api/coloquios/{id}/resultados` devolviendo la lista de candidatos con su `nota_final` (null si aún no tiene resultado registrado), paginada.

#### Scenario: Ver resultados de la convocatoria
- **WHEN** un COORDINADOR con `coloquios:ver` consulta `GET /api/coloquios/{id}/resultados`
- **THEN** el sistema devuelve todos los candidatos de la convocatoria con `alumno_nombre`, `alumno_email` y `nota_final` (null si no registrada)

#### Scenario: Aislamiento multi-tenant en resultados
- **WHEN** se consultan resultados de una convocatoria
- **THEN** el sistema devuelve exclusivamente datos del tenant de la sesión activa

### Requirement: Exportar registro de resultados a CSV
El sistema SHALL exponer `GET /api/coloquios/{id}/resultados/export` que devuelva los resultados de la convocatoria en formato CSV descargable.

#### Scenario: Exportar CSV de resultados
- **WHEN** un COORDINADOR con `coloquios:ver` llama el endpoint de export
- **THEN** el sistema devuelve `StreamingResponse` con `Content-Type: text/csv` y columnas: alumno_nombre, alumno_email, nota_final
