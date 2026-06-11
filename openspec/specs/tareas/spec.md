# Tareas Specification

## Purpose
Internal task workflow between coordinators and teaching staff.

## Requirements

### Requirement: Task CRUD
The system MUST allow creating, reading, updating, and soft-deleting tasks.

#### Scenario: Create task
- GIVEN a coordinator with `tareas:gestionar` permission
- WHEN they create a task with description, criterio_cierre, and assignee
- THEN the task is persisted with estado=Pendiente and aprobada=False

#### Scenario: Update task
- GIVEN a task in estado=Pendiente
- WHEN the assigner updates description or criterio_cierre
- THEN the task reflects the changes

#### Scenario: Soft delete task
- GIVEN a task exists
- WHEN the assigner soft deletes it
- THEN deleted_at is set and the task is excluded from listings

### Requirement: State Machine
The system MUST enforce valid state transitions.

| From | To | Allowed By |
|------|----|------------|
| Pendiente | En progreso | Assignee |
| En progreso | Resuelta | Assignee |
| Resuelta | En progreso | Assigner (return) |
| Any | Cancelada | Assignee or Assigner |

#### Scenario: Advance state
- GIVEN a task in estado=Pendiente
- WHEN the assignee sets estado=En progreso
- THEN the transition succeeds

#### Scenario: Resolve task
- GIVEN a task in En progreso
- WHEN the assignee sets estado=Resuelta
- THEN estado becomes Resuelta

#### Scenario: Approve task
- GIVEN a task in Resuelta
- WHEN the assigner approves it
- THEN aprobada=True, revisada_por and revisada_at are set

#### Scenario: Return task
- GIVEN a task in Resuelta
- WHEN the assigner returns it with observation
- THEN devuelta=True, estado resets to En progreso, and the action is audited

#### Scenario: Invalid transition
- GIVEN a task in Resuelta
- WHEN the assignee tries to set estado=En progreso without return
- THEN the system returns 422

#### Scenario: Unauthorized state change
- GIVEN a task assigned to another user
- WHEN the current user tries to change its state
- THEN the system returns 403

### Requirement: Delegation
The system MUST allow reassigning a task to another docente.

#### Scenario: Delegate task
- GIVEN a task in Pendiente
- WHEN the assignee reassigns it to another docente
- THEN the new assignee sees the task and the old one does not

### Requirement: Filtering
The system MUST support paginated, indexed listing with filters.

#### Scenario: My tasks
- GIVEN a docente is logged in
- WHEN they request their tasks
- THEN only tasks where asignado_a equals their id are returned, paginated

#### Scenario: Admin filtered view
- GIVEN a coordinator with `tareas:gestionar`
- WHEN they list tasks filtering by docente, materia, estado, or free-text
- THEN the matching tasks are returned paginated

### Requirement: Audit
The system MUST audit all task lifecycle events.

#### Scenario: Audit creation
- GIVEN a task is created
- THEN an audit log entry with action TAREA_CREAR is recorded

#### Scenario: Audit approval
- GIVEN a task is approved
- THEN an audit log entry with action TAREA_APROBAR is recorded
