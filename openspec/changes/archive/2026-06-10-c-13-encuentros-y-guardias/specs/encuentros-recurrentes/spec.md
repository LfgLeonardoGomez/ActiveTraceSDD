# Encuentros Recurrentes Specification

## Purpose

Define the behavior of synchronous academic encounter scheduling: recurring slots that generate concrete instances, one-off encounters, instance editing, and HTML block generation for embedding in Moodle virtual classrooms.

## Requirements

### Requirement: Create Slot (Recurrent)

The system MUST allow creating a `SlotEncuentro` that defines a recurring encounter pattern. The request MUST include `materia_id`, `dia_semana`, `hora`, `fecha_inicio`, `cant_semanas`, and optionally `meet_url` and `titulo`. Upon creation, the system MUST automatically generate exactly `cant_semanas` `InstanciaEncuentro` rows in a single transaction, each with a computed `fecha` advancing weekly from `fecha_inicio` matching `dia_semana`.

#### Scenario: Create recurrent slot with 8 weeks

- GIVEN a `Materia` exists in the tenant
- WHEN a user with `encuentros:gestionar` creates a slot with `cant_semanas=8`, `dia_semana=Lunes`, `fecha_inicio=2026-03-09`
- THEN the system returns `201 Created` with the `SlotEncuentro`
- AND exactly 8 `InstanciaEncuentro` rows are created with dates: 2026-03-09, 2026-03-16, ..., 2026-04-27
- AND all instances have `estado=Programado`, `tenant_id` matching the actor's tenant, and `slot_id` pointing to the created slot

#### Scenario: Slot creation with `cant_semanas=0` creates one instance

- GIVEN a `Materia` exists in the tenant
- WHEN a user creates a slot with `cant_semanas=0` (or `fecha_unica` is provided)
- THEN exactly 1 `InstanciaEncuentro` is created with `slot_id` set
- AND the system treats this as a one-off encounter bound to a slot

#### Scenario: Slot creation cap exceeded

- GIVEN a `Materia` exists in the tenant
- WHEN a user creates a slot with `cant_semanas=53`
- THEN the system returns `422 Unprocessable Entity` with error: "cant_semanas must be between 1 and 52"
- AND no slot or instances are created

#### Scenario: Invalid materia on slot creation

- GIVEN a `materia_id` that does not exist or belongs to another tenant
- WHEN a user attempts to create a slot
- THEN the system returns `404 Not Found` or `422` referencing the invalid materia
- AND no slot or instances are created

#### Scenario: Unauthorized slot creation

- GIVEN a user without `encuentros:gestionar` permission
- WHEN the user attempts to create a slot
- THEN the system returns `403 Forbidden`
- AND no slot or instances are created

### Requirement: Create One-Off Encounter (Standalone Instance)

The system MUST allow creating a single `InstanciaEncuentro` without a `slot_id`. The request MUST include `materia_id`, `fecha`, `hora`, and optionally `titulo`, `meet_url`. The `slot_id` MUST be `NULL`.

#### Scenario: Create standalone one-off encounter

- GIVEN a `Materia` exists in the tenant
- WHEN a user with `encuentros:gestionar` creates an instance with `fecha=2026-05-01`, `hora=18:00`, `materia_id`, and no `slot_id`
- THEN the system returns `201 Created` with the `InstanciaEncuentro`
- AND `slot_id` is `NULL`
- AND `estado` is `Programado`

#### Scenario: Unauthorized one-off creation

- GIVEN a user without `encuentros:gestionar` permission
- WHEN the user attempts to create a standalone instance
- THEN the system returns `403 Forbidden`

### Requirement: Edit Instance

The system MUST allow editing fields of an `InstanciaEncuentro` independently of its slot and of other instances. Editable fields: `estado`, `meet_url`, `video_url`, `comentario`. Editing MUST NOT affect the slot or other instances.

#### Scenario: Mark instance as Realizado with video URL

- GIVEN an `InstanciaEncuentro` with `estado=Programado`
- WHEN a user with `encuentros:gestionar` sends `estado=Realizado`, `video_url=https://...`
- THEN the system returns `200 OK` with the updated instance
- AND the instance reflects the new estado and video_url
- AND the parent slot and sibling instances remain unchanged

#### Scenario: Cancel an instance

- GIVEN an `InstanciaEncuentro` with `estado=Programado`
- WHEN a user sets `estado=Cancelado`
- THEN the system returns `200 OK` with the updated instance
- AND the instance's estado is `Cancelado`
- AND other instances of the same slot remain `Programado`

#### Scenario: Edit instance with invalid estado

- GIVEN an `InstanciaEncuentro` exists
- WHEN a user sends `estado=Invalido`
- THEN the system returns `422 Unprocessable Entity`
- AND the instance is not modified

#### Scenario: Unauthorized instance edit

- GIVEN an `InstanciaEncuentro` exists
- WHEN a user without `encuentros:gestionar` attempts to edit it
- THEN the system returns `403 Forbidden`
- AND the instance is not modified

#### Scenario: Edit instance from another tenant

- GIVEN an `InstanciaEncuentro` belongs to tenant B
- WHEN a user from tenant A attempts to edit it
- THEN the system returns `404 Not Found` (tenant isolation)

### Requirement: List Instances

The system MUST list `InstanciaEncuentro` rows with filtering by `materia_id`, `cohorte_id`, `fecha` range, `estado`, and `slot_id`. Tenant isolation MUST be applied.

#### Scenario: List instances by materia and date range

- GIVEN 10 instances exist for materia M in the tenant
- WHEN a user with `encuentros:gestionar` lists instances with `materia_id=M`, `fecha_desde=2026-03-01`, `fecha_hasta=2026-03-31`
- THEN the system returns a paginated list containing only instances matching the filters
- AND all returned instances belong to the actor's tenant

#### Scenario: List instances across all materias (admin/coord view)

- GIVEN instances exist for multiple materias in the tenant
- WHEN a user with `encuentros:gestionar` lists instances without `materia_id` filter
- THEN the system returns instances from all materias within the tenant
- AND instances from other tenants are excluded

#### Scenario: Unauthorized list

- GIVEN a user without `encuentros:gestionar` permission
- WHEN the user attempts to list instances
- THEN the system returns `403 Forbidden`

### Requirement: Generate HTML Block

The system MUST provide an endpoint that returns an HTML fragment containing a table of upcoming `InstanciaEncuentro` rows for a given `materia_id` and optionally `slot_id`. The HTML MUST be semantic (no inline styles) with CSS classes for styling. A `?format=markdown` query parameter MUST return Markdown instead of HTML.

#### Scenario: Generate HTML block for a materia

- GIVEN 5 upcoming instances exist for materia M
- WHEN a user with `encuentros:gestionar` requests the HTML block for `materia_id=M`
- THEN the system returns `200 OK` with `Content-Type: text/html`
- AND the response body contains a `<table>` with rows showing date, time, title, and meet_url link
- AND instances with `estado=Cancelado` are marked visually

#### Scenario: Generate Markdown block

- GIVEN 3 upcoming instances exist for a slot
- WHEN a user requests the block with `?format=markdown`
- THEN the system returns `200 OK` with `Content-Type: text/markdown`
- AND the response body contains a Markdown table of the instances

#### Scenario: Generate block for empty set

- GIVEN no upcoming instances exist for materia M
- WHEN a user requests the HTML block for `materia_id=M`
- THEN the system returns `200 OK` with an empty table or placeholder message

#### Scenario: Unauthorized block generation

- GIVEN a user without `encuentros:gestionar` permission
- WHEN the user requests the HTML block
- THEN the system returns `403 Forbidden`

#### Scenario: Cross-tenant block isolation

- GIVEN instances exist for materia M in tenant B
- WHEN a user from tenant A requests the block for `materia_id=M`
- THEN the system returns `404 Not Found` or an empty result (tenant isolation)

### Requirement: Slot Encuentro CRUD

The system MUST support reading, updating, and soft-deleting `SlotEncuentro`. Editing a slot MUST NOT retroactively modify existing `InstanciaEncuentro` rows (RN-14). Soft-deleting a slot MUST soft-delete its associated instances.

#### Scenario: Update slot title

- GIVEN a `SlotEncuentro` with `titulo="Clases de repaso"` and 8 existing instances
- WHEN a user with `encuentros:gestionar` updates `titulo` to `"Clases de repaso - nuevo título"`
- THEN the slot's `titulo` is updated
- AND all existing `InstanciaEncuentro` rows remain unchanged

#### Scenario: Soft-delete slot cascades to instances

- GIVEN a `SlotEncuentro` with 5 instances
- WHEN a user soft-deletes the slot
- THEN the slot's `deleted_at` is set
- AND all associated `InstanciaEncuentro` rows have `deleted_at` set

#### Scenario: List slots

- GIVEN multiple slots exist in the tenant
- WHEN a user with `encuentros:gestionar` lists slots
- THEN the system returns a paginated list of slots
- AND slots from other tenants are excluded

#### Scenario: Unauthorized slot operations

- GIVEN a user without `encuentros:gestionar` permission
- WHEN the user attempts to update or delete a slot
- THEN the system returns `403 Forbidden`

## MODIFIED Requirements

None.

## REMOVED Requirements

None.

## RENAMED Requirements

None.
