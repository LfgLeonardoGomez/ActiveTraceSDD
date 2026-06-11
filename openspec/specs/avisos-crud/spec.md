# Avisos CRUD Specification

## Purpose
Management of system announcements (avisos) by COORDINADOR and ADMIN.

## Requirements

### Requirement: Create Aviso
The system MUST allow COORDINADOR/ADMIN with `avisos:publicar` to create an aviso via POST /api/avisos. The request body SHALL be a Pydantic schema with `extra='forbid'` containing: alcance (Global|PorMateria|PorCohorte|PorRol), materia_id (nullable), cohorte_id (nullable), rol_destino (nullable = all), severidad (Info|Advertencia|Crítico), titulo, cuerpo (rich text), inicio_en, fin_en, orden, activo, requiere_ack. The system MUST set tenant_id from the JWT session. The system MUST reject requests with fields not declared.

#### Scenario: Successful creation
- GIVEN a COORDINADOR with `avisos:publicar`
- WHEN POST /api/avisos with valid payload
- THEN the aviso is persisted with tenant_id matching the session
- AND the response returns the created aviso with id

#### Scenario: Forbidden for ALUMNO
- GIVEN an ALUMNO without `avisos:publicar`
- WHEN POST /api/avisos
- THEN the system returns 403

### Requirement: Update Aviso
The system MUST allow COORDINADOR/ADMIN with `avisos:publicar` to update an aviso via PATCH /api/avisos/{id}. Only editable fields (alcance, materia_id, cohorte_id, rol_destino, severidad, titulo, cuerpo, inicio_en, fin_en, orden, activo, requiere_ack) MAY be modified. The system MUST NOT allow changing id or tenant_id. The system MUST verify the aviso belongs to the user's tenant.

#### Scenario: Update titulo and activo
- GIVEN an existing aviso in the same tenant
- WHEN PATCH /api/avisos/{id} with {"titulo": "Nuevo", "activo": false}
- THEN the aviso is updated
- AND the response reflects the changes

#### Scenario: Update id is rejected
- GIVEN an existing aviso
- WHEN PATCH /api/avisos/{id} with {"id": "new-uuid"}
- THEN the system returns 400 because id is not editable

### Requirement: Delete Aviso
The system MUST allow COORDINADOR/ADMIN with `avisos:publicar` to soft-delete an aviso via DELETE /api/avisos/{id}. The system MUST set deleted_at to the current timestamp. The system MUST verify the aviso belongs to the user's tenant.

#### Scenario: Soft delete
- GIVEN an existing aviso
- WHEN DELETE /api/avisos/{id}
- THEN the aviso's deleted_at is set
- AND subsequent GET /api/avisos/{id} returns 404 for management

#### Scenario: Delete non-tenant aviso
- GIVEN an aviso from another tenant
- WHEN DELETE /api/avisos/{id}
- THEN the system returns 404

### Requirement: List Avisos (management)
The system MUST provide GET /api/avisos paginated for COORDINADOR/ADMIN with `avisos:publicar`. The list MUST be filtered by tenant_id. It MAY be filtered by alcance, activo, severidad. The system MUST include avisos regardless of vigencia window (inicio_en..fin_en) for management.

#### Scenario: Filter by severidad
- GIVEN two avisos with different severidad
- WHEN GET /api/avisos?severidad=Crítico
- THEN only the Crítico aviso is returned

#### Scenario: Pagination
- GIVEN 25 avisos
- WHEN GET /api/avisos?limit=10&offset=0
- THEN 10 items are returned and total_count is 25

### Requirement: Get Aviso by ID
The system MUST provide GET /api/avisos/{id} for COORDINADOR/ADMIN with `avisos:publicar`. The system MUST verify the aviso belongs to the user's tenant and is not soft-deleted.

#### Scenario: Retrieve existing aviso
- GIVEN an existing aviso
- WHEN GET /api/avisos/{id}
- THEN the aviso details are returned

#### Scenario: Retrieve soft-deleted aviso
- GIVEN a soft-deleted aviso
- WHEN GET /api/avisos/{id}
- THEN the system returns 404
