## ADDED Requirements

### Requirement: Crear cohorte
El sistema SHALL permitir a un usuario con permiso `estructura:gestionar` crear una cohorte para una carrera de su tenant. La cohorte solo puede crearse si la carrera está en estado `Activa`. La unicidad se garantiza por `(tenant_id, carrera_id, nombre)`.

#### Scenario: Creación exitosa
- **WHEN** un ADMIN envía `POST /api/v1/admin/cohortes` con `carrera_id`, `nombre="MAR-2026"`, `anio=2026`, `vig_desde=2026-03-01`
- **THEN** el sistema crea la cohorte con `estado=Activa` y responde HTTP 201 con el recurso creado

#### Scenario: Carrera inactiva impide crear cohorte
- **WHEN** un ADMIN intenta crear una cohorte referenciando una carrera con `estado=Inactiva`
- **THEN** el sistema responde HTTP 409 con mensaje que indica que la carrera está inactiva

#### Scenario: Nombre duplicado en la misma carrera y tenant
- **WHEN** un ADMIN intenta crear una cohorte con `nombre="MAR-2026"` en una carrera donde ya existe una cohorte con ese nombre
- **THEN** el sistema responde HTTP 409

#### Scenario: Mismo nombre en otra carrera del mismo tenant no es conflicto
- **WHEN** un ADMIN crea una cohorte con `nombre="MAR-2026"` en la carrera B, y ese nombre ya existe en la carrera A del mismo tenant
- **THEN** el sistema crea la cohorte exitosamente — la unicidad es por `(tenant_id, carrera_id, nombre)`

#### Scenario: Mismo nombre en otra carrera de otro tenant no es conflicto
- **WHEN** el tenant A tiene `carrera_id=X, nombre="MAR-2026"` y el tenant B intenta crear la misma combinación en su propia carrera
- **THEN** el sistema crea la cohorte del tenant B exitosamente

#### Scenario: Carrera de otro tenant
- **WHEN** un ADMIN del tenant A intenta crear una cohorte referenciando un `carrera_id` del tenant B
- **THEN** el sistema responde HTTP 404 (la carrera no existe en el scope del tenant A)

#### Scenario: Sin permiso estructura:gestionar
- **WHEN** un usuario sin el permiso `estructura:gestionar` intenta crear una cohorte
- **THEN** el sistema responde HTTP 403

---

### Requirement: Listar cohortes paginadas
El sistema SHALL retornar la lista de cohortes del tenant autenticado, con soporte de filtro por `carrera_id` y/o `estado`. Las cohortes con soft delete no deben aparecer.

#### Scenario: Listado completo del tenant
- **WHEN** un ADMIN envía `GET /api/v1/admin/cohortes`
- **THEN** el sistema responde HTTP 200 con las cohortes del tenant, sin cohortes de otros tenants ni borradas

#### Scenario: Filtro por carrera
- **WHEN** un ADMIN envía `GET /api/v1/admin/cohortes?carrera_id={id}`
- **THEN** el sistema retorna solo las cohortes asociadas a esa carrera del tenant

#### Scenario: Filtro por estado Activa
- **WHEN** un ADMIN envía `GET /api/v1/admin/cohortes?estado=Activa`
- **THEN** el sistema retorna solo las cohortes con `estado=Activa`

---

### Requirement: Obtener detalle de cohorte
El sistema SHALL retornar el detalle completo de una cohorte por UUID, únicamente si pertenece al tenant del actor autenticado.

#### Scenario: Detalle existente
- **WHEN** un ADMIN envía `GET /api/v1/admin/cohortes/{id}` con un UUID válido de su tenant
- **THEN** el sistema responde HTTP 200 con todos los campos incluyendo el `carrera_id` y datos de vigencia

#### Scenario: Cohorte de otro tenant
- **WHEN** un ADMIN del tenant A solicita el detalle de una cohorte del tenant B
- **THEN** el sistema responde HTTP 404

---

### Requirement: Editar cohorte
El sistema SHALL permitir editar los campos `nombre`, `anio`, `vig_desde`, `vig_hasta` de una cohorte existente. El cambio de nombre debe respetar la unicidad `(tenant_id, carrera_id, nombre)`.

#### Scenario: Edición exitosa
- **WHEN** un ADMIN envía `PUT /api/v1/admin/cohortes/{id}` con una `vig_hasta` nueva
- **THEN** el sistema actualiza el campo y responde HTTP 200

#### Scenario: Cambio de nombre duplicado
- **WHEN** un ADMIN intenta cambiar el `nombre` de una cohorte a un nombre que ya usa otra cohorte de la misma carrera y tenant
- **THEN** el sistema responde HTTP 409

---

### Requirement: Cambiar estado de cohorte (activa/inactiva)
El sistema SHALL permitir cambiar el estado de una cohorte entre `Activa` e `Inactiva`.

#### Scenario: Desactivar cohorte activa
- **WHEN** un ADMIN envía `PUT /api/v1/admin/cohortes/{id}` con `estado=Inactiva`
- **THEN** el sistema cambia el estado a `Inactiva` y responde HTTP 200

#### Scenario: Reactivar cohorte inactiva con carrera activa
- **WHEN** un ADMIN intenta reactivar una cohorte cuya carrera está en estado `Activa`
- **THEN** el sistema cambia el estado a `Activa` y responde HTTP 200

#### Scenario: Reactivar cohorte con carrera inactiva
- **WHEN** un ADMIN intenta reactivar una cohorte cuya carrera está en estado `Inactiva`
- **THEN** el sistema responde HTTP 409 (no se puede abrir una cohorte bajo carrera inactiva)

---

### Requirement: Eliminar cohorte (soft delete)
El sistema SHALL implementar la eliminación de cohortes como soft delete. La cohorte no aparece en listados tras ser eliminada.

#### Scenario: Eliminación exitosa
- **WHEN** un ADMIN envía `DELETE /api/v1/admin/cohortes/{id}`
- **THEN** el sistema setea `deleted_at` y responde HTTP 204

#### Scenario: Cohorte eliminada no aparece en listado
- **WHEN** un ADMIN consulta `GET /api/v1/admin/cohortes` después de eliminar una cohorte
- **THEN** la cohorte eliminada no aparece en el resultado
