## ADDED Requirements

### Requirement: Crear carrera
El sistema SHALL permitir a un usuario con permiso `estructura:gestionar` crear una carrera nueva para su tenant, proporcionando un código único y un nombre descriptivo. El código del tenant identifica al tenant del actor autenticado (JWT) — no se acepta `tenant_id` como parámetro de la petición.

#### Scenario: Creación exitosa
- **WHEN** un ADMIN envía `POST /api/v1/admin/carreras` con `codigo="TUPAD"` y `nombre="Tecnicatura Universitaria en Programación"`
- **THEN** el sistema crea la carrera con `estado=Activa`, la asigna al `tenant_id` del JWT y responde con el recurso creado (HTTP 201) incluyendo el UUID generado

#### Scenario: Código duplicado en el mismo tenant
- **WHEN** un ADMIN intenta crear una carrera con un `codigo` que ya existe en su tenant
- **THEN** el sistema responde HTTP 409 con un mensaje que indica que el código ya está en uso en este tenant

#### Scenario: Código duplicado en otro tenant no es conflicto
- **WHEN** un ADMIN del tenant A crea una carrera con `codigo="TUPAD"` y ese código ya existe en el tenant B
- **THEN** el sistema crea la carrera exitosamente (HTTP 201) — la unicidad es por tenant, no global

#### Scenario: Sin permiso estructura:gestionar
- **WHEN** un usuario con rol que NO tiene el permiso `estructura:gestionar` intenta crear una carrera
- **THEN** el sistema responde HTTP 403

#### Scenario: Campos obligatorios ausentes
- **WHEN** un ADMIN envía `POST /api/v1/admin/carreras` sin el campo `codigo`
- **THEN** el sistema responde HTTP 422 (validación Pydantic)

---

### Requirement: Listar carreras paginadas
El sistema SHALL retornar la lista de carreras del tenant autenticado, con soporte de paginación y filtro opcional por estado. Las carreras borradas (soft delete) no deben aparecer.

#### Scenario: Listado básico
- **WHEN** un ADMIN envía `GET /api/v1/admin/carreras`
- **THEN** el sistema responde HTTP 200 con una lista de carreras del tenant, sin incluir carreras de otros tenants ni carreras con `deleted_at` no nulo

#### Scenario: Filtro por estado Activa
- **WHEN** un ADMIN envía `GET /api/v1/admin/carreras?estado=Activa`
- **THEN** el sistema responde únicamente las carreras con `estado=Activa` del tenant

#### Scenario: Paginación con limit/offset
- **WHEN** un ADMIN envía `GET /api/v1/admin/carreras?limit=10&offset=0`
- **THEN** el sistema responde a lo sumo 10 carreras y un indicador del total

#### Scenario: Aislamiento entre tenants
- **WHEN** el ADMIN del tenant B consulta la lista de carreras
- **THEN** el sistema no devuelve carreras del tenant A aunque tengan el mismo código

---

### Requirement: Obtener detalle de carrera
El sistema SHALL retornar el detalle completo de una carrera por su UUID, únicamente si pertenece al tenant del actor autenticado.

#### Scenario: Detalle existente
- **WHEN** un ADMIN envía `GET /api/v1/admin/carreras/{id}` con un UUID de una carrera de su tenant
- **THEN** el sistema responde HTTP 200 con todos los campos de la carrera

#### Scenario: Carrera de otro tenant
- **WHEN** un ADMIN del tenant A intenta obtener el detalle de una carrera del tenant B usando su UUID
- **THEN** el sistema responde HTTP 404 (el recurso no existe en el scope del tenant)

#### Scenario: UUID inexistente
- **WHEN** un ADMIN envía `GET /api/v1/admin/carreras/{id}` con un UUID que no existe
- **THEN** el sistema responde HTTP 404

---

### Requirement: Editar carrera
El sistema SHALL permitir editar el nombre y/o el código de una carrera existente. El cambio de código debe respetar la unicidad `(tenant_id, codigo)`.

#### Scenario: Edición exitosa de nombre
- **WHEN** un ADMIN envía `PUT /api/v1/admin/carreras/{id}` con un `nombre` nuevo
- **THEN** el sistema actualiza el campo `nombre` y responde HTTP 200 con el recurso actualizado

#### Scenario: Cambio de código a uno ya existente en el tenant
- **WHEN** un ADMIN intenta cambiar el código de una carrera a un código que ya usa otra carrera del mismo tenant
- **THEN** el sistema responde HTTP 409

#### Scenario: Edición de carrera de otro tenant
- **WHEN** un ADMIN del tenant A intenta editar una carrera del tenant B
- **THEN** el sistema responde HTTP 404

---

### Requirement: Cambiar estado de carrera (activa/inactiva)
El sistema SHALL permitir cambiar el estado de una carrera entre `Activa` e `Inactiva`. Una carrera con cohortes activas NO puede desactivarse.

#### Scenario: Desactivar carrera sin cohortes activas
- **WHEN** un ADMIN envía `PUT /api/v1/admin/carreras/{id}` con `estado=Inactiva` y la carrera no tiene cohortes en estado `Activa`
- **THEN** el sistema cambia el estado a `Inactiva` y responde HTTP 200

#### Scenario: Desactivar carrera con cohortes activas
- **WHEN** un ADMIN intenta desactivar una carrera que tiene al menos una cohorte en estado `Activa`
- **THEN** el sistema responde HTTP 409 con mensaje que indica que existen cohortes activas bajo esta carrera

#### Scenario: Reactivar carrera inactiva
- **WHEN** un ADMIN envía `PUT /api/v1/admin/carreras/{id}` con `estado=Activa` sobre una carrera inactiva
- **THEN** el sistema cambia el estado a `Activa` y responde HTTP 200

---

### Requirement: Eliminar carrera (soft delete)
El sistema SHALL implementar la eliminación de carreras como soft delete (setting `deleted_at`). La carrera no aparece en listados ni en búsquedas tras ser eliminada.

#### Scenario: Eliminación exitosa
- **WHEN** un ADMIN envía `DELETE /api/v1/admin/carreras/{id}`
- **THEN** el sistema setea `deleted_at` con el timestamp actual y responde HTTP 204

#### Scenario: Carrera eliminada no aparece en listado
- **WHEN** un ADMIN consulta `GET /api/v1/admin/carreras` después de eliminar una carrera
- **THEN** la carrera eliminada no aparece en el resultado
