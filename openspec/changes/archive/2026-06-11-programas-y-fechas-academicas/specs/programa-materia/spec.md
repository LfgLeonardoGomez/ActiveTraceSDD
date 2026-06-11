## ADDED Requirements

### Requirement: Programa de materia se asocia a materia carrera y cohorte
El sistema SHALL permitir gestionar documentos de programa oficiales vinculados a una combinación específica de materia, carrera y cohorte.

#### Scenario: Alta de programa exitosa
- **WHEN** un usuario con permiso `estructura:gestionar` envía una petición POST a `/api/programas` con `materia_id`, `carrera_id`, `cohorte_id`, `titulo` y `referencia_archivo`
- **THEN** el sistema crea un `ProgramaMateria` y retorna 201 con el objeto creado

#### Scenario: Unicidad de programa por combinación
- **WHEN** se intenta crear un programa para una combinación `(materia_id, carrera_id, cohorte_id)` que ya tiene un programa activo
- **THEN** el sistema rechaza la petición con 409 Conflict

#### Scenario: Lectura de programa por materia
- **WHEN** un usuario con permiso `estructura:ver` realiza GET a `/api/programas?materia_id=<id>`
- **THEN** el sistema retorna la lista de programas asociados a esa materia, filtrados por tenant

#### Scenario: Baja lógica de programa
- **WHEN** un usuario con permiso `estructura:gestionar` envía DELETE a `/api/programas/<id>`
- **THEN** el sistema marca `deleted_at` y no lo incluye en listados posteriores

### Requirement: Fechas académicas se registran por materia cohorte y tipo
El sistema SHALL permitir registrar, editar y listar fechas de evaluaciones (parcial, TP, coloquio, recuperatorio) por materia y cohorte, con número de instancia y período.

#### Scenario: Alta de fecha académica
- **WHEN** un usuario con permiso `estructura:gestionar` envía POST a `/api/fechas-academicas` con `materia_id`, `cohorte_id`, `tipo`, `numero`, `periodo`, `fecha` y `titulo`
- **THEN** el sistema crea una `FechaAcademica` y retorna 201

#### Scenario: Listado tabular de fechas por materia
- **WHEN** un usuario con permiso `estructura:ver` realiza GET a `/api/fechas-academicas?materia_id=<id>`
- **THEN** el sistema retorna las fechas ordenadas por `tipo`, `numero`, `fecha`

#### Scenario: Edición de fecha académica
- **WHEN** un usuario con permiso `estructura:gestionar` envía PUT a `/api/fechas-academicas/<id>`
- **THEN** el sistema actualiza los campos editables y retorna 200

#### Scenario: Eliminación de fecha académica
- **WHEN** un usuario con permiso `estructura:gestionar` envía DELETE a `/api/fechas-academicas/<id>`
- **THEN** el sistema aplica soft delete y retorna 204

### Requirement: Generación de fragmento para aula virtual
El sistema SHALL generar un fragmento de contenido HTML con las fechas académicas de una materia y cohorte, listo para publicar en el aula virtual del LMS.

#### Scenario: Generación de fragmento exitosa
- **WHEN** un usuario con permiso `estructura:ver` realiza GET a `/api/fechas-academicas/<materia_id>/<cohorte_id>/lms-content`
- **THEN** el sistema retorna un string HTML con tabla de fechas (tipo, número, fecha, título)

#### Scenario: Generación sin fechas
- **WHEN** se solicita el fragmento para una materia/cohorte sin fechas registradas
- **THEN** el sistema retorna un mensaje indicando que no hay fechas configuradas

## MODIFIED Requirements
- (sin modificaciones)

## REMOVED Requirements
- (sin remociones)
