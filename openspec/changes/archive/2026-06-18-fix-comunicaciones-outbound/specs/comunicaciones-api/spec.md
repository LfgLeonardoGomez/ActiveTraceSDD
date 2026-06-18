# Delta for comunicaciones-api

> Change: fix-comunicaciones-outbound · Domains modified: template rendering, approval filter
> Hard rules validated: multi-tenancy repo scoping (unchanged), approval gate (defense-in-depth via R-17), tests with real DB (no mocks), PII AES-256 (unchanged).

---

## MODIFIED Requirements

### Requirement: Preview de mensaje antes de encolar

The system SHALL expose `POST /api/comunicaciones/preview` that renders the message with substitution variables resolved for a list of recipients without persisting any data (RN-16).

The public placeholder syntax `{{alumno.nombre}}` and `{{alumno.email}}` MUST be accepted exactly as documented. Internally, before invoking `string.Template.substitute`, the service MUST normalize dotted key names to underscore-flat identifiers (`alumno.nombre` → `alumno_nombre`) in both the variable context dict and the template text. The public syntax contract MUST NOT change.

A placeholder that does not belong to the allowed set (`alumno_nombre`, `alumno_email`) MUST produce HTTP 422 with a message that names the unrecognized variable.

(Previously: this requirement had no normalization step; `_renderizar_plantilla` converted `{{` → `${` and `}}` → `}` producing `${alumno.nombre}`, which `string.Template` rejected — every preview call with documented syntax returned 422.)

#### Scenario: Preview renders documented dot-notation variables correctly

- GIVEN a tenant with at least one alumno (nombre="Ana García", email="ana@example.com")
- WHEN a PROFESOR sends `POST /api/comunicaciones/preview` with `plantilla_asunto="Hola {{alumno.nombre}}"`, `plantilla_cuerpo="Tu email es {{alumno.email}}"`, and `destinatarios=[{alumno_id, nombre: "Ana García", email: "ana@example.com"}]`
- THEN the system returns HTTP 200 with `asunto="Hola Ana García"` and `cuerpo="Tu email es ana@example.com"` for that recipient
- AND no record is created in the `comunicacion` table

#### Scenario: Preview with multiple recipients — each message personalized

- GIVEN two alumnos: alumno A (nombre="Carlos", email="carlos@example.com") and alumno B (nombre="María", email="maria@example.com")
- WHEN a PROFESOR sends `POST /api/comunicaciones/preview` with both recipients and the template `"Hola {{alumno.nombre}}, te escribimos a {{alumno.email}}"`
- THEN the system returns exactly two rendered items: one with Carlos's data substituted and one with María's data substituted
- AND neither item contains any unresolved `{{...}}` placeholder

#### Scenario: Preview with unknown variable returns 422 with clear message

- GIVEN a valid authenticated PROFESOR
- WHEN the request body includes `plantilla_asunto="Hola {{alumno.inexistente}}"` with at least one recipient
- THEN the system returns HTTP 422
- AND the response body identifies `alumno.inexistente` (or its normalized form) as an unrecognized variable

#### Scenario: Preview does not persist data

- WHEN `POST /api/comunicaciones/preview` is called with valid data
- THEN no row is created in the `comunicacion` table and no entry is written to `AuditLog`

#### Scenario: Variable inválida en plantilla (existing — unchanged)

- WHEN the template contains `{{variable_inexistente}}`
- THEN the system returns 422 indicating which variables are not available

---

## ADDED Requirements

### Requirement: Approval filter on get_pendientes_para_despacho

The system SHALL filter `get_pendientes_para_despacho` by `aprobado = True` in the SQL WHERE clause. This MUST apply regardless of tenant approval settings. The docstring MUST accurately describe the filter applied.

This requirement is defense-in-depth: the live dispatch path uses `get_todos_pendientes_elegibles` (which already filters correctly); this closes the trap for any future caller of the lower-level method.

**Hard rule**: multi-tenancy scoping via `BaseRepository` tenant filter remains unchanged. The `aprobado` predicate is an additional AND condition.

#### Scenario: get_pendientes_para_despacho excludes unapproved rows

- GIVEN a tenant with two `Comunicacion` rows in state `Pendiente`: one with `aprobado=True` and one with `aprobado=False`
- WHEN `get_pendientes_para_despacho` is called for that tenant
- THEN only the row with `aprobado=True` is returned
- AND the row with `aprobado=False` is absent from the result set

#### Scenario: get_pendientes_para_despacho respects tenant isolation

- GIVEN two tenants each with one `Pendiente`/`aprobado=True` comunicacion
- WHEN `get_pendientes_para_despacho` is called scoped to tenant A
- THEN only tenant A's row is returned (existing multi-tenancy guarantee, verified as unchanged)
