# Guardias Specification

## Purpose

Define the behavior of tutor duty-shift registration: TUTOR registers their own guardias, COORDINADOR/ADMIN queries and exports the global record per tenant.

## Requirements

### Requirement: Register Guardia

The system MUST allow a TUTOR to register a `Guardia` for their own assignment context. The request MUST include `fecha`, `materia_id`, `carrera_id`, `cohorte_id`, `descripcion`, and optionally `horario`. The `asignacion_id` MUST be resolved from the user's own active assignment for the given context. The initial `estado` MUST be `Pendiente`.

#### Scenario: TUTOR registers a guardia for their materia

- GIVEN a TUTOR has a valid `Asignacion` to `materia_id=M`, `carrera_id=C`, `cohorte_id=H`
- WHEN the TUTOR with `guardias:registrar` posts a guardia with `fecha=2026-04-15`, `materia_id=M`, `carrera_id=C`, `cohorte_id=H`, `descripcion="Consulta de TP"`, `horario="14:00–14:45"`
- THEN the system returns `201 Created` with the `Guardia`
- AND `estado` is `Pendiente`
- AND `asignacion_id` matches the TUTOR's assignment for that context
- AND `tenant_id` matches the actor's tenant

#### Scenario: Register guardia with invalid horario format

- GIVEN a TUTOR has a valid assignment
- WHEN the TUTOR posts a guardia with `horario="14h00"` (invalid format)
- THEN the system returns `422 Unprocessable Entity`
- AND the guardia is not created

#### Scenario: Register guardia for materia not assigned to user

- GIVEN a TUTOR does not have an active assignment for `materia_id=M`
- WHEN the TUTOR attempts to register a guardia for `materia_id=M`
- THEN the system returns `403 Forbidden` or `422` indicating the user is not assigned to that materia

#### Scenario: Unauthorized guardia registration

- GIVEN a user without `guardias:registrar` permission
- WHEN the user attempts to register a guardia
- THEN the system returns `403 Forbidden`

#### Scenario: Register guardia with invalid materia

- GIVEN a `materia_id` that does not exist in the tenant
- WHEN a TUTOR attempts to register a guardia
- THEN the system returns `404 Not Found` or `422`

### Requirement: List Guardias

The system MUST allow listing `Guardia` records with filtering by `fecha` range, `materia_id`, `tutor_id` (via `asignacion_id`), and `estado`. Tenant isolation MUST be applied. COORDINADOR/ADMIN MUST see all guardias in the tenant. TUTOR/PROFESOR MUST see only their own guardias.

#### Scenario: COORDINADOR lists all guardias in tenant

- GIVEN 20 guardias exist across multiple materias and tutors in the tenant
- WHEN a COORDINADOR with `encuentros:gestionar` lists guardias with no filters
- THEN the system returns a paginated list containing all 20 guardias
- AND guardias from other tenants are excluded

#### Scenario: TUTOR lists own guardias

- GIVEN a TUTOR has registered 5 guardias
- WHEN the TUTOR with `guardias:registrar` lists guardias
- THEN the system returns only the 5 guardias linked to the TUTOR's assignments
- AND guardias from other tutors are excluded

#### Scenario: Filter guardias by date range and materia

- GIVEN guardias exist in April 2026 for materia M
- WHEN a user lists guardias with `fecha_desde=2026-04-01`, `fecha_hasta=2026-04-30`, `materia_id=M`
- THEN the system returns only guardias matching the date range and materia

#### Scenario: Unauthorized list

- GIVEN a user without `encuentros:gestionar` or `guardias:registrar` permission
- WHEN the user attempts to list guardias
- THEN the system returns `403 Forbidden`

#### Scenario: Cross-tenant list isolation

- GIVEN guardias exist in tenant B
- WHEN a user from tenant A lists guardias
- THEN the system returns an empty list or excludes tenant B's records

### Requirement: Export Guardias

The system MUST support exporting guardias as CSV or XLSX via a `?formato=csv|xlsx` query parameter. The export MUST include non-PII fields: tutor name, materia, carrera, cohorte, dia, horario, estado, comentarios. The export MUST respect the same filters and tenant isolation as the list endpoint.

#### Scenario: Export guardias as CSV

- GIVEN 10 guardias exist in the tenant
- WHEN a user with `encuentros:gestionar` requests `GET /api/v1/guardias?formato=csv`
- THEN the system returns `200 OK` with `Content-Type: text/csv`
- AND the response body is a valid CSV with a header row and 10 data rows
- AND all fields are non-PII

#### Scenario: Export guardias as XLSX

- GIVEN 10 guardias exist in the tenant
- WHEN a user requests `GET /api/v1/guardias?formato=xlsx`
- THEN the system returns `200 OK` with `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- AND the response body is a valid XLSX file

#### Scenario: Export with filters applied

- GIVEN 20 guardias exist, but only 5 match `materia_id=M` and `estado=Realizada`
- WHEN a user exports with `formato=csv&materia_id=M&estado=Realizada`
- THEN the exported file contains exactly 5 rows

#### Scenario: Unauthorized export

- GIVEN a user without `encuentros:gestionar` or `guardias:registrar` permission
- WHEN the user attempts to export guardias
- THEN the system returns `403 Forbidden`

#### Scenario: Export empty set

- GIVEN no guardias exist in the tenant
- WHEN a user exports with `formato=csv`
- THEN the system returns `200 OK` with a CSV containing only the header row

## MODIFIED Requirements

None.

## REMOVED Requirements

None.

## RENAMED Requirements

None.
