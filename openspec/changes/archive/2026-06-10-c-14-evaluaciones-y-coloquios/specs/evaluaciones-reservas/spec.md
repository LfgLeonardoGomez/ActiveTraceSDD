## ADDED Requirements

### Requirement: ALUMNO reserva turno en convocatoria
El sistema SHALL permitir a un ALUMNO habilitado reservar un turno (`ReservaEvaluacion`) en una convocatoria vía `POST /api/coloquios/{id}/reservas`. La reserva requiere que el alumno esté en el padrón de candidatos y que haya cupo disponible para el día solicitado.

#### Scenario: Reserva exitosa con cupo disponible
- **WHEN** un ALUMNO con `coloquios:reservar` envía `POST /api/coloquios/{id}/reservas` con una `fecha_hora` válida cuyo día tiene cupo disponible y el alumno está en el padrón de candidatos
- **THEN** el sistema crea la `ReservaEvaluacion` con `estado=Activa` y devuelve 201

#### Scenario: Sin cupo disponible para el día solicitado
- **WHEN** un ALUMNO intenta reservar un día cuyo cupo ya está completo (`count(reservas activas) >= cupo_por_dia`)
- **THEN** el sistema devuelve 409 Conflict con mensaje `sin_cupo_disponible`

#### Scenario: Alumno no está en el padrón de candidatos
- **WHEN** un ALUMNO intenta reservar turno pero no está en `evaluacion_candidato` de esa convocatoria
- **THEN** el sistema devuelve 403 Forbidden

#### Scenario: Alumno ya tiene reserva activa en la misma convocatoria
- **WHEN** un ALUMNO que ya tiene una `ReservaEvaluacion` con `estado=Activa` intenta crear otra reserva para la misma convocatoria
- **THEN** el sistema devuelve 409 Conflict con mensaje `reserva_duplicada`

### Requirement: Cancelar reserva propia (ALUMNO)
El sistema SHALL permitir a un ALUMNO cancelar su propia reserva activa vía `DELETE /api/coloquios/{evaluacion_id}/reservas/{reserva_id}`, transicionando el estado a `Cancelada` y liberando el cupo.

#### Scenario: Cancelación exitosa
- **WHEN** un ALUMNO con `coloquios:reservar` cancela su propia reserva activa
- **THEN** el sistema transiciona `estado` a `Cancelada`, libera el cupo y devuelve 200

#### Scenario: Intento de cancelar reserva de otro alumno
- **WHEN** un ALUMNO intenta cancelar la reserva de otro usuario
- **THEN** el sistema devuelve 403 Forbidden

#### Scenario: Reserva ya cancelada
- **WHEN** se intenta cancelar una `ReservaEvaluacion` con `estado=Cancelada`
- **THEN** el sistema devuelve 409 Conflict con mensaje `reserva_ya_cancelada`

### Requirement: Cancelar reserva por coordinación
El sistema SHALL permitir a COORDINADOR o ADMIN cancelar cualquier reserva activa de la convocatoria vía el mismo endpoint `DELETE /api/coloquios/{evaluacion_id}/reservas/{reserva_id}`.

#### Scenario: COORDINADOR cancela reserva de un alumno
- **WHEN** un COORDINADOR con `coloquios:gestionar` cancela una reserva activa
- **THEN** el sistema transiciona a `Cancelada` y devuelve 200 independientemente de quién sea el alumno

### Requirement: Consultar agenda de reservas de una convocatoria
El sistema SHALL exponer `GET /api/coloquios/{id}/reservas` devolviendo la lista paginada de reservas activas y canceladas de la convocatoria, visible para COORDINADOR, ADMIN, PROFESOR y TUTOR.

#### Scenario: Ver agenda de la convocatoria
- **WHEN** un COORDINADOR con `coloquios:ver` consulta `GET /api/coloquios/{id}/reservas`
- **THEN** el sistema devuelve la lista de reservas con alumno_nombre, fecha_hora y estado

#### Scenario: ALUMNO no puede ver la agenda completa
- **WHEN** un ALUMNO intenta acceder a `GET /api/coloquios/{id}/reservas`
- **THEN** el sistema devuelve 403 Forbidden (el ALUMNO solo ve su propia reserva)
