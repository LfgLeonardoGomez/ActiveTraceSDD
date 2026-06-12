# Tareas Specification

## Purpose
Internal task workflow between coordinators and teaching staff — covering both backend API (CRUD, state machine, delegation, audit) and frontend UI (mis tareas, asignación, admin global, comments, polling).

---

## Backend

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

---

## Frontend

> Workflow de tareas internas: vista de mis tareas, asignación a docentes y administración global con transiciones de estado y comentarios.

### REQ-TA-01: Vista de mis tareas

El componente `TareaCard` muestra las tareas asignadas al usuario, consumiendo `GET /api/v1/tareas/mis-tareas`. Soporta filtros por contexto académico y permite iniciar el flujo de delegación.

#### Scenario 1: Vista con tareas asignadas
- GIVEN el usuario tiene tareas asignadas (TUTOR, PROFESOR o COORDINADOR)
- WHEN navega a `/coordinacion/tareas`
- THEN se muestra una lista de `TareaCard` con: título, materia, asignador, estado (pendiente/en_proceso/completada/aprobada/rechazada), fecha de creación, fecha límite
- AND cada card muestra un `TareaStatusBadge` con el color correspondiente al estado
- AND las cards están ordenadas por fecha de creación descendente

#### Scenario 2: Filtros en mis tareas
- GIVEN la lista de tareas está visible
- WHEN el usuario filtra por estado ("pendiente"), materia, o rango de fechas
- THEN la query incluye los parámetros de filtro
- AND la lista se actualiza
- AND un contador muestra "{N} tareas encontradas"

#### Scenario 3: Sin tareas asignadas
- GIVEN el usuario no tiene tareas
- WHEN navega a la sección
- THEN se muestra "No tenés tareas asignadas"
- AND un mensaje "Cuando te asignen una tarea, aparecerá acá"

#### Scenario 4: Actualizar estado de tarea propia
- GIVEN una `TareaCard` con estado "pendiente"
- WHEN el usuario hace clic en el badge de estado y selecciona "en_proceso"
- THEN se abre un breve campo de comentario opcional
- WHEN confirma
- THEN `PUT /api/v1/tareas/{id}` se llama con `{ estado: "en_proceso" }`
- AND el badge se actualiza al nuevo estado
- AND un toast "Estado actualizado" se muestra

#### Scenario 5: Completar tarea con comentario
- GIVEN una tarea en estado "en_proceso"
- WHEN el usuario hace clic en "Completar"
- THEN el `TareaCommentThread` se expande permitiendo agregar un comentario de cierre
- WHEN escribe un comentario y confirma
- THEN `PUT /api/v1/tareas/{id}` se llama con `{ estado: "completada", comentario: "..." }`
- AND la card se actualiza

#### Scenario 6: Polling mientras tarea no está en estado terminal
- GIVEN hay tareas en estados no terminales (pendiente, en_proceso)
- WHILE el componente está montado
- THEN `refetchInterval` está activo (cada 30s) para refrescar estados
- WHEN todas las tareas pasan a estados terminales (completada, aprobada, rechazada)
- THEN el polling se detiene automáticamente

#### Scenario 7: Loading state
- GIVEN el componente monta
- WHILE los datos cargan
- THEN 3 skeleton cards con shimmer se muestran

#### Scenario 8: Error state
- GIVEN la API falla
- THEN se muestra "Error al cargar tus tareas" con botón "Reintentar"

#### Scenario 9: Tarea con fecha límite vencida
- GIVEN una tarea tiene fecha_límite anterior a hoy y estado no terminal
- THEN la `TareaCard` muestra un indicador visual de "Vencida" en rojo
- AND el tooltip muestra "Fecha límite: {fecha}"

### REQ-TA-02: Asignar tarea a un docente

El componente `TareaForm` permite crear y asignar una tarea a otro miembro del equipo docente, consumiendo `POST /api/v1/tareas`.

#### Scenario 1: Asignar tarea exitosa
- GIVEN el usuario tiene permiso `tareas:asignar`
- WHEN navega a `/coordinacion/tareas/asignar`
- THEN `TareaForm` muestra campos: asignado_a (selector de búsqueda de docentes), materia (dropdown opcional), título, descripción (textarea), fecha_límite (datepicker), prioridad (baja/media/alta)
- WHEN completa todos los campos y envía
- THEN `POST /api/v1/tareas` se llama
- AND en 201, se redirige a `/coordinacion/tareas`
- AND un toast "Tarea asignada a {docente}" se muestra

#### Scenario 2: Validación — campos requeridos
- GIVEN el formulario de asignación
- WHEN el usuario intenta enviar sin seleccionar docente o sin título
- THEN validación Zod muestra "Seleccioná un docente" y "El título es requerido"
- AND el envío se bloquea

#### Scenario 3: Búsqueda de docente
- GIVEN el selector de docente
- WHEN el usuario escribe al menos 3 caracteres
- THEN se muestra un dropdown con resultados
- WHEN selecciona un docente
- THEN el `docente_id` se asigna al formulario

#### Scenario 4: Fecha límite en el pasado
- GIVEN el campo fecha_límite
- WHEN el usuario selecciona una fecha anterior a hoy
- THEN validación Zod muestra "La fecha límite debe ser futura"
- AND el envío se bloquea

#### Scenario 5: Loading state en envío
- GIVEN el usuario envió el formulario
- WHILE el POST se procesa
- THEN el botón muestra spinner con "Asignando tarea..."
- AND todos los campos se deshabilitan

#### Scenario 6: Error state
- GIVEN el POST falla
- THEN se muestra "Error al asignar la tarea" con el mensaje del backend
- AND el formulario conserva los valores

### REQ-TA-03: Administración global de tareas

El componente `TareaTable` permite a COORDINADOR/ADMIN ver todas las tareas del tenant y cambiar su estado, consumiendo `GET /api/v1/tareas` y `PUT /api/v1/tareas/{id}`.

#### Scenario 1: Vista global con filtros
- GIVEN el usuario tiene permiso `tareas:admin`
- WHEN navega a `/coordinacion/tareas/admin`
- THEN se muestra una tabla con columnas: Título, Asignado a, Asignador, Materia, Estado, Prioridad, Fecha límite, Creada, Acciones
- AND filtros disponibles: docente asignado, docente asignador, materia, estado, búsqueda libre

#### Scenario 2: Cambiar estado de tarea desde admin
- GIVEN la tabla global está visible
- WHEN el ADMIN/COORDINADOR hace clic en el menú de acciones de una tarea
- THEN un dropdown muestra opciones: "Aprobar", "Rechazar", "Reasignar"
- WHEN selecciona "Aprobar"
- THEN `PUT /api/v1/tareas/{id}` se llama con `{ estado: "aprobada" }`
- AND la tabla se actualiza
- AND un toast "Tarea aprobada" se muestra

#### Scenario 3: Rechazar tarea con comentario
- GIVEN el menú de acciones de una tarea en estado "completada"
- WHEN el usuario selecciona "Rechazar"
- THEN un modal pide un comentario obligatorio: "Indicá el motivo del rechazo"
- WHEN ingresa el motivo y confirma
- THEN `PUT /api/v1/tareas/{id}` se llama con `{ estado: "rechazada", comentario: "..." }`
- AND la tarea vuelve a aparecer en la vista "Mis tareas" del docente asignado

#### Scenario 4: Sin tareas en el tenant
- GIVEN no hay tareas creadas
- WHEN el usuario navega a admin
- THEN se muestra "No hay tareas registradas en el sistema"

#### Scenario 5: Búsqueda libre
- GIVEN la tabla global
- WHEN el usuario escribe en el campo de búsqueda libre
- THEN la query incluye `?q=...`
- AND la tabla se filtra por título, descripción o docente

#### Scenario 6: Hilo de comentarios
- GIVEN la tabla global
- WHEN el usuario hace clic en "Comentarios" de una tarea
- THEN se expande `TareaCommentThread` mostrando el historial de comentarios ordenado cronológicamente
- AND el usuario puede agregar un nuevo comentario

#### Scenario 7: Loading state
- GIVEN el componente monta
- WHILE los datos cargan
- THEN tabla esqueleto se muestra
- AND los filtros están deshabilitados

#### Scenario 8: Error state
- GIVEN la API falla
- THEN se muestra "Error al cargar tareas" con reintento
