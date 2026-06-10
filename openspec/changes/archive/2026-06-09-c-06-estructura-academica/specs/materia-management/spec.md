## ADDED Requirements

### Requirement: Crear materia
El sistema SHALL permitir a un usuario con permiso `estructura:gestionar` crear una materia nueva en el catálogo del tenant. El catálogo es único por tenant (ADR-006). La unicidad se garantiza por `(tenant_id, codigo)`. El `tenant_id` se obtiene del JWT — no se acepta como parámetro de la petición.

#### Scenario: Creación exitosa
- **WHEN** un ADMIN envía `POST /api/v1/admin/materias` con `codigo="PROG_I"` y `nombre="Programación I"`
- **THEN** el sistema crea la materia con `estado=Activa`, asignada al `tenant_id` del JWT, y responde HTTP 201 con el recurso creado

#### Scenario: Código duplicado en el mismo tenant
- **WHEN** un ADMIN intenta crear una materia con un `codigo` que ya existe en su tenant
- **THEN** el sistema responde HTTP 409 con mensaje que indica que el código ya está en uso

#### Scenario: Código duplicado en otro tenant no es conflicto
- **WHEN** el tenant A tiene una materia `codigo="PROG_I"` y el tenant B intenta crear su propia materia con el mismo código
- **THEN** el sistema crea la materia del tenant B exitosamente (la unicidad es por tenant)

#### Scenario: Sin permiso estructura:gestionar
- **WHEN** un usuario sin el permiso `estructura:gestionar` intenta crear una materia
- **THEN** el sistema responde HTTP 403

#### Scenario: Campos obligatorios ausentes
- **WHEN** un ADMIN envía `POST /api/v1/admin/materias` sin el campo `nombre`
- **THEN** el sistema responde HTTP 422

#### Scenario: Campos extra en el body son rechazados
- **WHEN** un ADMIN envía `POST /api/v1/admin/materias` con un campo no declarado en el schema
- **THEN** el sistema responde HTTP 422 (`extra='forbid'` de Pydantic)

---

### Requirement: Listar materias paginadas
El sistema SHALL retornar la lista de materias del catálogo del tenant autenticado, con paginación y filtro opcional por estado. Las materias con soft delete no aparecen.

#### Scenario: Listado básico
- **WHEN** un ADMIN envía `GET /api/v1/admin/materias`
- **THEN** el sistema responde HTTP 200 con las materias del tenant, sin incluir materias de otros tenants

#### Scenario: Filtro por estado Activa
- **WHEN** un ADMIN envía `GET /api/v1/admin/materias?estado=Activa`
- **THEN** el sistema retorna solo las materias con `estado=Activa` del tenant

#### Scenario: Paginación
- **WHEN** un ADMIN envía `GET /api/v1/admin/materias?limit=20&offset=0`
- **THEN** el sistema retorna a lo sumo 20 materias y el total del catálogo del tenant

#### Scenario: Aislamiento entre tenants en listado
- **WHEN** el ADMIN del tenant B consulta la lista de materias
- **THEN** el sistema no devuelve materias del tenant A

---

### Requirement: Obtener detalle de materia
El sistema SHALL retornar el detalle completo de una materia por UUID, únicamente si pertenece al catálogo del tenant del actor autenticado.

#### Scenario: Detalle existente
- **WHEN** un ADMIN envía `GET /api/v1/admin/materias/{id}` con un UUID de materia de su tenant
- **THEN** el sistema responde HTTP 200 con todos los campos de la materia

#### Scenario: Materia de otro tenant
- **WHEN** un ADMIN del tenant A solicita el detalle de una materia del tenant B
- **THEN** el sistema responde HTTP 404

#### Scenario: UUID inexistente
- **WHEN** un ADMIN envía `GET /api/v1/admin/materias/{id}` con UUID que no existe en su tenant
- **THEN** el sistema responde HTTP 404

---

### Requirement: Editar materia
El sistema SHALL permitir editar el nombre y/o el código de una materia. El cambio de código debe respetar la unicidad `(tenant_id, codigo)`.

#### Scenario: Edición exitosa de nombre
- **WHEN** un ADMIN envía `PUT /api/v1/admin/materias/{id}` con un `nombre` nuevo
- **THEN** el sistema actualiza el `nombre` y responde HTTP 200

#### Scenario: Cambio de código a uno ya existente
- **WHEN** un ADMIN intenta cambiar el `codigo` de una materia a un código que ya usa otra materia del mismo tenant
- **THEN** el sistema responde HTTP 409

#### Scenario: Edición de materia de otro tenant
- **WHEN** un ADMIN del tenant A intenta editar una materia del tenant B
- **THEN** el sistema responde HTTP 404

---

### Requirement: Cambiar estado de materia (activa/inactiva)
El sistema SHALL permitir cambiar el estado de una materia entre `Activa` e `Inactiva`. El estado es un atributo de ciclo de vida; las materias inactivas permanecen en el catálogo pero son filtradas por defecto en los listados de selección de módulos dependientes.

#### Scenario: Desactivar materia activa
- **WHEN** un ADMIN envía `PUT /api/v1/admin/materias/{id}` con `estado=Inactiva`
- **THEN** el sistema cambia el estado a `Inactiva` y responde HTTP 200

#### Scenario: Reactivar materia inactiva
- **WHEN** un ADMIN envía `PUT /api/v1/admin/materias/{id}` con `estado=Activa`
- **THEN** el sistema cambia el estado a `Activa` y responde HTTP 200

---

### Requirement: Eliminar materia del catálogo (soft delete)
El sistema SHALL implementar la eliminación de materias como soft delete. La materia no aparece en listados tras ser eliminada.

#### Scenario: Eliminación exitosa
- **WHEN** un ADMIN envía `DELETE /api/v1/admin/materias/{id}` sobre una materia de su tenant
- **THEN** el sistema setea `deleted_at` con el timestamp actual y responde HTTP 204

#### Scenario: Materia eliminada no aparece en listado
- **WHEN** un ADMIN consulta `GET /api/v1/admin/materias` después de eliminar una materia
- **THEN** la materia eliminada no aparece en el resultado

#### Scenario: Eliminar materia de otro tenant
- **WHEN** un ADMIN del tenant A intenta eliminar una materia del tenant B
- **THEN** el sistema responde HTTP 404
