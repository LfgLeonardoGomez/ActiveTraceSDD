# Tasks: C-23 — Frontend Coordinación

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~3500 |
| New files | ~66 |
| Modified files | 2 (App.tsx, Sidebar.tsx) |

---

## Phase 1: Foundation — Types + API Services + Routing

### Task 1.1: Create `types/equipos.types.ts`
- **File**: `frontend/src/features/coordinacion/types/equipos.types.ts`
- [x] `Equipo` — materia, carrera, cohorte, roles, vigencia, estado
- [x] `Asignacion` — docente, materia, carrera, cohorte, rol, fechas, estado
- [x] `AsignacionRequest` — docente_id, materia_id, carrera_id, cohorte_id, rol, fechas
- [x] `AsignacionMasivaRequest extends Omit<AsignacionRequest, 'docente_id'>` — docente_ids[]
- [x] `UsuarioDocente` — id, nombre, email, rol, regional, activo
- [x] `ClonarEquipoRequest` — origen/destino con materia_id + cohorte_id

### Task 1.2: Create `types/estructura.types.ts`
- **File**: `frontend/src/features/coordinacion/types/estructura.types.ts`
- [x] `Carrera` — codigo, nombre, activa, creada
- [x] `Cohorte` — nombre, year, fecha_desde, fecha_hasta, estado
- [x] `Programa` — materia, carrera, cohorte, titulo, filename, fecha_subida
- [x] `Evaluacion` — materia, cohorte, tipo (parcial/tp/coloquio), instancia, fecha, titulo

### Task 1.3: Create `types/encuentros.types.ts`
- **File**: `frontend/src/features/coordinacion/types/encuentros.types.ts`
- [x] `Encuentro` — materia, docente, fecha, hora, estado (programado/realizado/cancelado), enlace, grabacion
- [x] `SerieRecurrenteRequest` — materia_id, dia_semana (1-5), horario, fecha_inicio, semanas (1-16), titulo
- [x] `Guardia` — tutor, materia, dia, horario_desde/hasta, estado, comentarios

### Task 1.4: Create `types/coloquios.types.ts`
- **File**: `frontend/src/features/coordinacion/types/coloquios.types.ts`
- [x] `MetricasColoquios` — total_alumnos_cargados, instancias_activas, reservas_activas, notas_registradas
- [x] `Convocatoria` — materia, instancia, titulo, cohorte, dias[], estado, contadores
- [x] `ConvocatoriaDia` — fecha, cupo_maximo
- [x] `ImportResult` — imported_count, errors[]
- [x] `Reserva` — alumno, convocatoria, dia, horario, estado

### Task 1.5: Create `types/tareas.types.ts`
- **File**: `frontend/src/features/coordinacion/types/tareas.types.ts`
- [x] `TareaEstado` — 'pendiente' | 'en_proceso' | 'completada' | 'aprobada' | 'rechazada'
- [x] `Tarea` — titulo, descripcion, asignado, asignador, materia, estado, prioridad, fechas, comentarios[]
- [x] `TareaComment` — autor, contenido, fecha
- [x] `TareaFilters` — estado, materia, fecha_desde, fecha_hasta, q

### Task 1.6: Create `types/avisos.types.ts`
- **File**: `frontend/src/features/coordinacion/types/avisos.types.ts`
- [x] `Aviso` — titulo, cuerpo, alcance (global/materia/cohorte), roles_destinatarios[], severidad, estado, vigencia, requiere_ack
- [x] `AvisoFormData` — all form fields with optional dates
- [x] `AckEntry` — destinatario, rol, leido, fecha_lectura

### Task 1.7: Create `types/monitor.types.ts`
- **File**: `frontend/src/features/coordinacion/types/monitor.types.ts`
- [x] `MonitorFilters` — nombre, email, comision, regional, materia, actividad, fecha_desde/hasta, q
- [x] `MonitorEntry` — alumno, nombre, email, comision, regional, materia, actividad, estado, ultima_actividad
- [x] `AuditoriaEntry` — fecha_hora, docente, rol, accion, materia, registros_afectados, ip, detalle

### Task 1.8: Create `services/equipos.api.ts`
- **File**: `frontend/src/features/coordinacion/services/equipos.api.ts`
- [x] `getMisEquipos(filters?): Promise<Equipo[]>` — `GET /api/v1/equipos/mis-equipos`
- [x] `getUsuarios(): Promise<UsuarioDocente[]>` — `GET /api/v1/equipos/usuarios`
- [x] `crearUsuario(data): Promise<UsuarioDocente>` — `POST /api/v1/equipos/usuarios`
- [x] `actualizarUsuario(id, data): Promise<UsuarioDocente>` — `PUT /api/v1/equipos/usuarios/{id}`
- [x] `getAsignaciones(filters?): Promise<Asignacion[]>` — `GET /api/v1/equipos/asignaciones`
- [x] `crearAsignacion(data): Promise<Asignacion>` — `POST /api/v1/equipos/asignaciones`
- [x] `asignacionMasiva(data): Promise<{ count: number; errors?: any[] }>` — `POST /api/v1/equipos/asignaciones/masiva`
- [x] `clonarEquipo(data): Promise<{ asignaciones_creadas: number }>` — `POST /api/v1/equipos/clonar`
- [x] `actualizarVigencia(data): Promise<{ updated_count: number }>` — `PUT /api/v1/equipos/vigencia`
- [x] `getExportUrl(equipoId): string` — returns export URL string for direct download

### Task 1.9: Create `services/estructura.api.ts`
- **File**: `frontend/src/features/coordinacion/services/estructura.api.ts`
- [x] `getCarreras(): Promise<Carrera[]>` — `GET /api/v1/estructura/carreras`
- [x] `crearCarrera(data): Promise<Carrera>` — `POST /api/v1/estructura/carreras`
- [x] `actualizarCarrera(id, data): Promise<Carrera>` — `PUT /api/v1/estructura/carreras/{id}`
- [x] `getCohortes(filters?): Promise<Cohorte[]>` — `GET /api/v1/estructura/cohortes`
- [x] `crearCohorte(data): Promise<Cohorte>` — `POST /api/v1/estructura/cohortes`
- [x] `actualizarCohorte(id, data): Promise<Cohorte>` — `PUT /api/v1/estructura/cohortes/{id}`
- [x] `getProgramas(): Promise<Programa[]>` — `GET /api/v1/estructura/programas`
- [x] `subirPrograma(formData): Promise<Programa>` — `POST /api/v1/estructura/programas` (FormData)
- [x] `eliminarPrograma(id): Promise<void>` — `DELETE /api/v1/estructura/programas/{id}`
- [x] `descargarPrograma(id): string` — returns download URL
- [x] `getEvaluaciones(filters?): Promise<Evaluacion[]>` — `GET /api/v1/estructura/evaluaciones`
- [x] `crearEvaluacion(data): Promise<Evaluacion>` — `POST /api/v1/estructura/evaluaciones`
- [x] `actualizarEvaluacion(id, data): Promise<Evaluacion>` — `PUT /api/v1/estructura/evaluaciones/{id}`

### Task 1.10: Create `services/encuentros.api.ts`
- **File**: `frontend/src/features/coordinacion/services/encuentros.api.ts`
- [x] `getEncuentros(filters?): Promise<Encuentro[]>` — `GET /api/v1/encuentros`
- [x] `crearEncuentro(data): Promise<Encuentro>` — `POST /api/v1/encuentros`
- [x] `crearRecurrente(data): Promise<{ instancias: Encuentro[]; count: number }>` — `POST /api/v1/encuentros/recurrente`
- [x] `editarEncuentro(id, data): Promise<Encuentro>` — `PUT /api/v1/encuentros/{id}`
- [x] `getContenidoAula(filters?): Promise<any>` — `GET /api/v1/encuentros/contenido-aula`
- [x] `getGuardias(filters?): Promise<Guardia[]>` — `GET /api/v1/encuentros/guardias`
- [x] `registrarGuardia(data): Promise<Guardia>` — `POST /api/v1/encuentros/guardias`

### Task 1.11: Create `services/coloquios.api.ts`
- **File**: `frontend/src/features/coordinacion/services/coloquios.api.ts`
- [x] `getMetricas(): Promise<MetricasColoquios>` — `GET /api/v1/coloquios/metricas`
- [x] `getConvocatorias(filters?): Promise<Convocatoria[]>` — `GET /api/v1/coloquios`
- [x] `crearConvocatoria(data): Promise<Convocatoria>` — `POST /api/v1/coloquios`
- [x] `getConvocatoriaDetail(id): Promise<Convocatoria>` — `GET /api/v1/coloquios/{id}`
- [x] `importarAlumnos(formData): Promise<ImportResult>` — `POST /api/v1/coloquios/importar-alumnos` (FormData)
- [x] `getAdminConvocatorias(): Promise<Convocatoria[]>` — `GET /api/v1/coloquios/admin`
- [x] `cerrarConvocatoria(id): Promise<Convocatoria>` — `PUT /api/v1/coloquios/admin/{id}`

### Task 1.12: Create `services/tareas.api.ts`
- **File**: `frontend/src/features/coordinacion/services/tareas.api.ts`
- [x] `getMisTareas(filters?): Promise<Tarea[]>` — `GET /api/v1/tareas/mis-tareas`
- [x] `getTareasAdmin(filters?): Promise<Tarea[]>` — `GET /api/v1/tareas`
- [x] `asignarTarea(data): Promise<Tarea>` — `POST /api/v1/tareas`
- [x] `actualizarEstadoTarea(id, data): Promise<Tarea>` — `PUT /api/v1/tareas/{id}`

### Task 1.13: Create `services/avisos.api.ts`
- **File**: `frontend/src/features/coordinacion/services/avisos.api.ts`
- [x] `getAvisos(filters?): Promise<Aviso[]>` — `GET /api/v1/avisos`
- [x] `crearAviso(data): Promise<Aviso>` — `POST /api/v1/avisos`
- [x] `editarAviso(id, data): Promise<Aviso>` — `PUT /api/v1/avisos/{id}`
- [x] `eliminarAviso(id): Promise<void>` — `DELETE /api/v1/avisos/{id}`
- [x] `confirmarAck(id): Promise<void>` — `POST /api/v1/avisos/{id}/ack`

### Task 1.14: Create `services/monitor.api.ts`
- **File**: `frontend/src/features/coordinacion/services/monitor.api.ts`
- [x] `getMonitorGeneral(filters, page): Promise<{ data: MonitorEntry[]; total: number; page: number; total_pages: number }>` — `GET /api/v1/analisis/monitor/general`
- [x] `getAuditoria(filters, page): Promise<{ data: AuditoriaEntry[]; total: number; page: number; total_pages: number }>` — `GET /api/v1/analisis/monitor/auditoria`

### Task 1.15: Create `CoordinacionLayout` component
- **File**: `frontend/src/features/coordinacion/components/CoordinacionLayout.tsx`
- [x] Section sub-navigation bar with links to the 7 domains
- [x] Renders `<Outlet />` for domain content
- [x] Active link highlighting based on current route
- [x] Responsive layout (sub-nav collapses on mobile)

### Task 1.16: Create `CoordinacionHome` dashboard
- **File**: `frontend/src/features/coordinacion/pages/CoordinacionHome.tsx`
- [x] Landing dashboard with KPI cards across domains
- [x] Quick-action cards for common flows (crear aviso, asignar tarea, etc.)
- [x] Permission-gated sections (hide admin-only cards from non-ADMIN)

### Task 1.17: Add routes in `App.tsx`
- **File**: `frontend/src/App.tsx`
- [x] Import `CoordinacionLayout` and all page components
- [x] Insert `/coordinacion` route block under `<Route element={<Layout />}>`
- [x] Nested routes for all 7 domains with their sub-routes per design §4

### Task 1.18: Update `Sidebar.tsx` with Coordinación section
- **File**: `frontend/src/shared/components/Sidebar.tsx`
- [x] Replace existing `/equipos` entry with `/coordinacion/equipos` (permission: `equipos:ver`)
- [x] Add section header "Coordinación" with 7 grouped nav entries
- [x] Each entry gated by its permission: `estructura:gestionar`, `encuentros:ver`, `coloquios:ver`, `tareas:ver`, `avisos:ver`, `monitor:ver`
- [x] Verify icons exist in lucide-react (Calendar, GraduationCap, ClipboardCheck, Megaphone, Activity from Q5)

---

## Phase 2: Equipos Docentes

### Task 2.1: Create `hooks/useEquipos.ts`
- **File**: `frontend/src/features/coordinacion/hooks/useEquipos.ts`
- [x] `useMisEquipos(filters?)` — `useQuery<Equipo[]>` key `['coordinacion', 'equipos', 'mis-equipos', filters]`, polling disabled
- [x] `useUsuarios()` — `useQuery<UsuarioDocente[]>` key `['coordinacion', 'equipos', 'usuarios']`, enabled only for ADMIN
- [x] `useAsignaciones(filters?)` — `useQuery<Asignacion[]>` key `['coordinacion', 'equipos', 'asignaciones', filters]`
- [x] `useCrearAsignacion()` — `useMutation`, onSuccess invalidates `['coordinacion', 'equipos', 'asignaciones']` and `['coordinacion', 'equipos', 'mis-equipos']`
- [x] `useAsignacionMasiva()` — `useMutation`, onSuccess invalidates `['coordinacion', 'equipos', 'asignaciones']`
- [x] `useClonarEquipo()` — `useMutation`, onSuccess invalidates `['coordinacion', 'equipos', 'asignaciones']`
- [x] `useActualizarVigencia()` — `useMutation`, onSuccess invalidates `['coordinacion', 'equipos', 'asignaciones']` and `['coordinacion', 'equipos', 'mis-equipos']`
- [x] `useCrearUsuario()` — `useMutation`, onSuccess invalidates `['coordinacion', 'equipos', 'usuarios']`
- [x] `useActualizarUsuario()` — `useMutation`, onSuccess invalidates `['coordinacion', 'equipos', 'usuarios']`

### Task 2.2: Create `EquipoCard` component
- **File**: `frontend/src/features/coordinacion/components/equipos/EquipoCard.tsx`
- [x] Summary card for mis-equipos view: materia, carrera, cohorte, roles, vigencia, estado
- [x] States: loading (skeleton shimmer), empty ("No tenés equipos asignados"), error ("Error al cargar tus equipos" + "Reintentar")
- [x] Agrupado por materia×cohorte (REQ-EQ-01 Scenario 1)
- [x] Contador "Mostrando {N} asignaciones" (REQ-EQ-01 Scenario 1)

### Task 2.3: Create `EquipoTable` component
- **File**: `frontend/src/features/coordinacion/components/equipos/EquipoTable.tsx`
- [x] Table: Docente, Materia, Carrera, Cohorte, Rol, Vigencia (desde/hasta), Estado
- [x] Paginated table
- [x] Filters: materia, carrera, cohorte, docente (search by name), rol
- [x] Empty state: "No hay asignaciones registradas" + "Crear primera asignación" (REQ-EQ-03 Scenario 2)
- [x] Loading: skeleton table (REQ-EQ-03 Scenario 7)
- [x] Error: "Error al cargar asignaciones" + "Reintentar" (REQ-EQ-03 Scenario 8)

### Task 2.4: Create `AsignacionForm` component
- **File**: `frontend/src/features/coordinacion/components/equipos/AsignacionForm.tsx`
- [x] Fields: docente (searchable selector), materia (dropdown), carrera, cohorte, rol, fecha_desde, fecha_hasta
- [x] Zod validation: all required, fecha_hasta > fecha_desde, docente already assigned check
- [x] Docente search: shows dropdown after 3+ chars (REQ-EQ-03 Scenario 6)
- [x] Successful creation: toast + close form + invalidate queries (REQ-EQ-03 Scenario 3)
- [x] Error: 409 inline "El docente ya está asignado" (REQ-EQ-03 Scenario 4)
- [x] Loading: spinner on submit button + disabled fields (REQ-EQ-03 Scenario 7)

### Task 2.5: Create `AsignacionMasivaForm` component
- **File**: `frontend/src/features/coordinacion/components/equipos/AsignacionMasivaForm.tsx`
- [x] Multi-select docentes (with search, chips, individual remove) (REQ-EQ-04 Scenario 3)
- [x] Fields: materia, carrera, cohorte, rol, fecha_desde, fecha_hasta
- [x] Zod validation: at least 1 docente required (REQ-EQ-04 Scenario 2)
- [x] Success summary: "Se crearon {N} asignaciones correctamente" + "Volver a asignaciones" (REQ-EQ-04 Scenario 1)
- [x] Partial errors: expandable error list (REQ-EQ-04 Scenario 4)
- [x] Loading: spinner + disabled fields (REQ-EQ-04 Scenario 6)
- [x] Network error: "Error de conexión" with preserved form values (REQ-EQ-04 Scenario 5)

### Task 2.6: Create `ClonarEquipoForm` component
- **File**: `frontend/src/features/coordinacion/components/equipos/ClonarEquipoForm.tsx`
- [x] Two selectors: "Equipo origen" and "Equipo destino" (materia×carrera×cohorte) (REQ-EQ-05 Scenario 1)
- [x] Zod validation: origen !== destino (REQ-EQ-05 Scenario 4)
- [x] Origen sin asignaciones: disable "Clonar equipo" button (REQ-EQ-05 Scenario 2)
- [x] Destino con asignaciones: warning + "Clonar de todas formas" confirmation (REQ-EQ-05 Scenario 3)
- [x] Success: "Equipo clonado correctamente — {N} asignaciones creadas" (REQ-EQ-05 Scenario 1)
- [x] Loading: spinner "Clonando equipo..." + disabled selectors (REQ-EQ-05 Scenario 5)
- [x] Error: message + editable form (REQ-EQ-05 Scenario 6)

### Task 2.7: Create `VigenciaEditor` component
- **File**: `frontend/src/features/coordinacion/components/equipos/VigenciaEditor.tsx`
- [x] Selector de equipo (materia×cohorte) + two datepickers (REQ-EQ-06 Scenario 1)
- [x] Zod validation: fecha_hasta > fecha_desde (REQ-EQ-06 Scenario 3)
- [x] Disabled button when no equipo selected (REQ-EQ-06 Scenario 2)
- [x] Confirmation dialog before update: show equipo name + affected count (REQ-EQ-06 Scenario 4)
- [x] Success: "Vigencia actualizada para {N} asignaciones" (REQ-EQ-06 Scenario 1)
- [x] Loading: spinner + disabled fields (REQ-EQ-06 Scenario 5)
- [x] Error: message + "Reintentar" (REQ-EQ-06 Scenario 6)

### Task 2.8: Create `ExportButton` component
- **File**: `frontend/src/features/coordinacion/components/equipos/ExportButton.tsx`
- [x] Selector de equipo + "Exportar CSV" button (REQ-EQ-07 Scenario 1)
- [x] Disabled when no equipo selected: "Seleccioná un equipo para exportar" (REQ-EQ-07 Scenario 2)
- [x] Download via Blob/Axios: `equipo_{materia}_{cohorte}.csv`
- [x] Loading: spinner "Exportando..." + disabled selector (REQ-EQ-07 Scenario 4)
- [x] Error: toast + preserved selection (REQ-EQ-07 Scenario 3)

### Task 2.9: Create `UsuarioForm` component (ADMIN only)
- **File**: `frontend/src/features/coordinacion/components/equipos/UsuarioForm.tsx`
- [x] Mode: create vs edit (precargado) (REQ-EQ-02 Scenario 2/5)
- [x] Fields: nombre, email, rol (PROFESOR/TUTOR/NEXO/COORDINADOR), regional, estado
- [x] Zod validation: all required, valid email format (REQ-EQ-02 Scenario 4)
- [x] Duplicate email: 409 inline "El email ya está registrado" (REQ-EQ-02 Scenario 3)
- [x] Success: toast + close form + table refresh (REQ-EQ-02 Scenario 2)

### Task 2.10: Create `UsuarioTable` component (ADMIN only)
- **File**: `frontend/src/features/coordinacion/components/equipos/UsuarioTable.tsx`
- [x] Columns: Nombre, Email, Rol, Regional, Estado (activo/inactivo), Última actualización (REQ-EQ-02 Scenario 1)
- [x] Paginated (50 per page) (REQ-EQ-02 Scenario 1)
- [x] "+ Nuevo usuario" button top-right (REQ-EQ-02 Scenario 1)
- [x] Edit icon per row (REQ-EQ-02 Scenario 5)
- [x] Toggle estado with confirmation dialog (REQ-EQ-02 Scenario 6)
- [x] Loading: skeleton table + disabled actions (REQ-EQ-02 Scenario 7)
- [x] Error: "Error al cargar usuarios" + "Reintentar" (REQ-EQ-02 Scenario 8)
- [x] Permission guard: hidden if not ADMIN (REQ-EQ-02 Scenario 9)

### Task 2.11: Create `EquiposPages.tsx`
- **File**: `frontend/src/features/coordinacion/pages/EquiposPages.tsx`
- [x] Sub-route layout with domain-specific navigation (secondary nav for usuarios, asignaciones, clonar, vigencia, exportar)
- [x] Renders `<Outlet />` for each sub-route
- [x] Permission guard on usuarios sub-route (ADMIN only)

---

## Phase 3: Estructura Académica

### Task 3.1: Create `hooks/useEstructura.ts`
- **File**: `frontend/src/features/coordinacion/hooks/useEstructura.ts`
- [x] `useCarreras()` — `useQuery<Carrera[]>` key `['coordinacion', 'estructura', 'carreras']`
- [x] `useCrearCarrera()` — `useMutation`, onSuccess invalidates `['coordinacion', 'estructura', 'carreras']`
- [x] `useActualizarCarrera()` — `useMutation`, onSuccess invalidates `['coordinacion', 'estructura', 'carreras']`
- [x] `useCohortes(filters?)` — `useQuery<Cohorte[]>` key `['coordinacion', 'estructura', 'cohortes', filters]`
- [x] `useCrearCohorte()` — `useMutation`, onSuccess invalidates `['coordinacion', 'estructura', 'cohortes']`
- [x] `useActualizarCohorte()` — `useMutation`, onSuccess invalidates `['coordinacion', 'estructura', 'cohortes']`
- [x] `useProgramas()` — `useQuery<Programa[]>` key `['coordinacion', 'estructura', 'programas']`
- [x] `useSubirPrograma()` — `useMutation`, onSuccess invalidates `['coordinacion', 'estructura', 'programas']`
- [x] `useEliminarPrograma()` — `useMutation`, onSuccess invalidates `['coordinacion', 'estructura', 'programas']`
- [x] `useEvaluaciones(filters?)` — `useQuery<Evaluacion[]>` key `['coordinacion', 'estructura', 'evaluaciones', filters]`
- [x] `useCrearEvaluacion()` — `useMutation`, onSuccess invalidates `['coordinacion', 'estructura', 'evaluaciones']`

### Task 3.2: Create `CarreraForm` component
- **File**: `frontend/src/features/coordinacion/components/estructura/CarreraForm.tsx`
- [x] Fields: codigo (short text, e.g., "LIC-MAT"), nombre (REQ-ES-01 Scenario 2)
- [x] Zod validation: required fields (REQ-ES-01 Scenario 9)
- [x] Duplicate code: 409 inline error (REQ-ES-01 Scenario 3)
- [x] Edit mode: precargado (REQ-ES-01 Scenario 4)
- [x] Toggle estado with confirmation (REQ-ES-01 Scenario 5)

### Task 3.3: Create `CohorteForm` component
- **File**: `frontend/src/features/coordinacion/components/estructura/CohorteForm.tsx`
- [x] Fields: nombre, año, fecha_desde, fecha_hasta, estado (REQ-ES-02 Scenario 2)
- [x] Duplicate name (same year): 409 inline (REQ-ES-02 Scenario 3)
- [x] Edit mode: precargado (REQ-ES-02 Scenario 4)

### Task 3.4: Create `ProgramaUploader` component
- **File**: `frontend/src/features/coordinacion/components/estructura/ProgramaUploader.tsx`
- [x] Form: materia (dropdown), carrera, cohorte, título, file input (PDF/DOC/DOCX) (REQ-ES-03 Scenario 1)
- [x] Client-side file type validation (REQ-ES-03 Scenario 2)
- [x] Upload via FormData with progress (REQ-ES-03 Scenario 1)
- [x] Program list table below uploader (REQ-ES-03 Scenario 4)
- [x] Download action (REQ-ES-03 Scenario 5)
- [x] Delete action with confirmation (REQ-ES-03 Scenario 6)
- [x] Loading: indeterminate progress bar + "Subiendo..." (REQ-ES-03 Scenario 8)
- [x] Error: preserved form values for retry (REQ-ES-03 Scenario 9)

### Task 3.5: Create `EvaluacionForm` + `EvaluacionCalendar` components
- **File**: `frontend/src/features/coordinacion/components/estructura/EvaluacionForm.tsx`
- [x] Fields: materia, cohorte, tipo (Parcial/TP/Coloquio), instancia, fecha, titulo (REQ-ES-04 Scenario 4)
- [x] Past date warning with confirmation (REQ-ES-04 Scenario 5)
- [x] Duplicate check: same materia×cohorte×tipo×instancia (REQ-ES-04 Scenario 7)
- [x] Edit mode: precargado (REQ-ES-04 Scenario 6)

- **File**: `frontend/src/features/coordinacion/components/estructura/EvaluacionCalendar.tsx`
- [x] Monthly calendar view with markers on evaluation dates (REQ-ES-04 Scenario 3)
- [x] Click on marked date shows tooltip with detail (REQ-ES-04 Scenario 3)
- [x] Filters persist between list/calendar toggle (REQ-ES-04 Scenario 3)

### Task 3.6: Create `EstructuraPages.tsx`
- **File**: `frontend/src/features/coordinacion/pages/EstructuraPages.tsx`
- [x] Sub-route layout with secondary nav: carreras, cohortes, programas, evaluaciones
- [x] Renders `<Outlet />` for each sub-section
- [x] Tab-style navigation with view toggle (lista/calendario) for evaluaciones

---

## Phase 4: Encuentros

### Task 4.1: Create `hooks/useEncuentros.ts`
- **File**: `frontend/src/features/coordinacion/hooks/useEncuentros.ts`
- [x] `useEncuentros(filters?)` — `useQuery<Encuentro[]>` key `['coordinacion', 'encuentros', 'list', filters]`
- [x] `useCrearRecurrente()` — `useMutation`, onSuccess invalidates `['coordinacion', 'encuentros', 'list']`
- [x] `useCrearEncuentro()` — `useMutation`, onSuccess invalidates `['coordinacion', 'encuentros', 'list']`
- [x] `useEditarEncuentro()` — `useMutation`, onSuccess invalidates `['coordinacion', 'encuentros', 'list']`
- [x] `useContenidoAula(filters?)` — `useQuery` key `['coordinacion', 'encuentros', 'contenido-aula', filters]`
- [x] `useGuardias(filters?)` — `useQuery<Guardia[]>` key `['coordinacion', 'encuentros', 'guardias', filters]`
- [x] `useRegistrarGuardia()` — `useMutation`, onSuccess invalidates `['coordinacion', 'encuentros', 'guardias']`

### Task 4.2: Create `EncuentroForm` component
- **File**: `frontend/src/features/coordinacion/components/encuentros/EncuentroForm.tsx`
- [x] Fields: materia, fecha (datepicker), hora (time picker), título, enlace (REQ-EN-02 Scenario 1)
- [x] Zod validation: fecha + hora required (REQ-EN-02 Scenario 2)
- [x] Past date: non-blocking warning (REQ-EN-02 Scenario 3)
- [x] On success: redirect to `/coordinacion/encuentros` with toast (REQ-EN-02 Scenario 1)

### Task 4.3: Create `EncuentroRecurrenteForm` component
- **File**: `frontend/src/features/coordinacion/components/encuentros/EncuentroRecurrenteForm.tsx`
- [x] Fields: materia, día de la semana (lun-vie), horario, fecha de inicio, semanas (1-16), título, enlace (REQ-EN-01 Scenario 1)
- [x] Zod validation: weeks 1-16 (REQ-EN-01 Scenario 2), valid URL (REQ-EN-01 Scenario 4)
- [x] Past date warning with confirmation (REQ-EN-01 Scenario 3)
- [x] Generation progress: inline spinner "Generando instancias..." → polling fallback if >2s (REQ-EN-01 Scenario 5, AD-06)
- [x] Success: "Serie creada correctamente — {N} instancias generadas" (REQ-EN-01 Scenario 1)
- [x] Error: message + preserved values (REQ-EN-01 Scenario 6)

### Task 4.4: Create `EncuentroTable` component
- **File**: `frontend/src/features/coordinacion/components/encuentros/EncuentroTable.tsx`
- [x] Columns: Materia, Cohorte, Docente, Fecha, Hora, Título, Estado, Enlace, Acciones (REQ-EN-05 Scenario 1)
- [x] Filters: materia, cohorte, docente, estado, date range (REQ-EN-05 Scenario 2-3)
- [x] Paginated (50 per page) (REQ-EN-05 Scenario 1)
- [x] Edit action navigates to edit route (REQ-EN-05 Scenario 7)
- [x] Empty: "No hay encuentros programados" (REQ-EN-05 Scenario 4)
- [x] Loading: skeleton table (REQ-EN-05 Scenario 5)
- [x] Error: message + "Reintentar" (REQ-EN-05 Scenario 6)

### Task 4.5: Create `EncuentroEditModal` component
- **File**: `frontend/src/features/coordinacion/components/encuentros/EncuentroEditModal.tsx`
- [x] Fields: estado (programado/realizado/cancelado), enlace, grabacion, comentario_interno (REQ-EN-03 Scenario 1)
- [x] Enlace de grabación disabled unless estado="realizado" (REQ-EN-03 Scenario 3)
- [x] Recurrent series: checkbox "Aplicar cambios a todas las instancias futuras" (REQ-EN-03 Scenario 2)
- [x] Cancel confirmation dialog (REQ-EN-03 Scenario 5)
- [x] Success: toast + table refresh (REQ-EN-03 Scenario 1)
- [x] Error: stay open for retry (REQ-EN-03 Scenario 4)

### Task 4.6: Create `ContenidoAulaPreview` component
- **File**: `frontend/src/features/coordinacion/components/encuentros/ContenidoAulaPreview.tsx`
- [x] Modal with filters: materia, cohorte, date range (REQ-EN-04 Scenario 1)
- [x] Generate button → GET endpoint → formatted preview table (REQ-EN-04 Scenario 1)
- [x] "Copiar al portapapeles" button (REQ-EN-04 Scenario 2)
- [x] Empty: "No hay encuentros programados en el período" (REQ-EN-04 Scenario 3)
- [x] Loading: spinner in preview area (REQ-EN-04 Scenario 4)
- [x] Error: message + modal stays open (REQ-EN-04 Scenario 5)

### Task 4.7: Create `GuardiaTable` component
- **File**: `frontend/src/features/coordinacion/components/encuentros/GuardiaTable.tsx`
- [x] Columns: Tutor, Materia, Carrera/Cohorte, Día, Horario, Estado, Comentarios (REQ-EN-06 Scenario 1)
- [x] Filters: tutor, materia, estado, date range (REQ-EN-06 Scenario 1/4)
- [x] "+ Registrar guardia" button → modal form (REQ-EN-06 Scenario 2)
- [x] Register modal: tutor (search), materia, día, horario desde/hasta, estado, comentarios (REQ-EN-06 Scenario 2)
- [x] Zod validation: horario_hasta > horario_desde (REQ-EN-06 Scenario 8)
- [x] Export CSV button (REQ-EN-06 Scenario 5)
- [x] Empty: "No hay guardias registradas" (REQ-EN-06 Scenario 3)
- [x] Loading: skeleton table (REQ-EN-06 Scenario 6)
- [x] Error: "Error al cargar guardias" + retry (REQ-EN-06 Scenario 7)

### Task 4.8: Create `EncuentrosPages.tsx`
- **File**: `frontend/src/features/coordinacion/pages/EncuentrosPages.tsx`
- [x] Sub-route layout with secondary nav: list, nuevo, recurrente, guardias
- [x] Renders `<Outlet />` for each sub-route
- [x] Edit route uses `useParams()` to get encuentroId

---

## Phase 5: Coloquios

### Task 5.1: Create `hooks/useColoquios.ts`
- **File**: `frontend/src/features/coordinacion/hooks/useColoquios.ts`
- [x] `useMetricasColoquios()` — `useQuery<MetricasColoquios>` key `['coordinacion', 'coloquios', 'metricas']`
- [x] `useConvocatorias(filters?)` — `useQuery<Convocatoria[]>` key `['coordinacion', 'coloquios', 'list', filters]`
- [x] `useConvocatoriaDetail(id)` — `useQuery<Convocatoria>` key `['coordinacion', 'coloquios', 'detail', id]`
- [x] `useCrearConvocatoria()` — `useMutation`, onSuccess invalidates `['coordinacion', 'coloquios', 'list']`
- [x] `useImportarAlumnos()` — `useMutation`, onSuccess invalidates `['coordinacion', 'coloquios', 'metricas']` and `['coordinacion', 'coloquios', 'detail']`
- [x] `useCerrarConvocatoria()` — `useMutation`, onSuccess invalidates `['coordinacion', 'coloquios', 'list']` and `['coordinacion', 'coloquios', 'admin']`
- [x] `useConvocatoriaAdmin()` — `useQuery` key `['coordinacion', 'coloquios', 'admin']`, enabled only for ADMIN

### Task 5.2: Create `MetricasPanel` component
- **File**: `frontend/src/features/coordinacion/components/coloquios/MetricasPanel.tsx`
- [x] 4 KPI cards: Total alumnos cargados, Instancias activas, Reservas activas, Notas registradas (REQ-CO-01 Scenario 1)
- [x] Zero state: all show "0" with grey icons (REQ-CO-01 Scenario 2)
- [x] Loading: 4 skeleton cards with shimmer (REQ-CO-01 Scenario 3)
- [x] Error: cards show "—" + "Error al cargar métricas" + "Reintentar" (REQ-CO-01 Scenario 4)
- [x] "Actualizar" button to refetch (REQ-CO-01 Scenario 5)

### Task 5.3: Create `ConvocatoriaForm` (3-step wizard)
- **File**: `frontend/src/features/coordinacion/components/coloquios/ConvocatoriaForm.tsx`
- [x] Step 1 "Datos generales": materia, cohorte, instancia (number), título (REQ-CO-03 Scenario 1)
- [x] Step 2 "Días y cupos": dynamic list of date + cupo_maximo entries (min 1) (REQ-CO-03 Scenario 1)
- [x] Step 3 "Confirmar": read-only summary of all data (REQ-CO-03 Scenario 1)
- [x] Step navigation: "Siguiente" / "Anterior" with Zod validation per step (REQ-CO-03 Scenarios 2-4)
- [x] Cupo validation: at least 1 per day (REQ-CO-03 Scenario 5)
- [x] State lifted to wizard parent (single FormData object) (AD-04)
- [x] Backward navigation preserves state (REQ-CO-03 Scenario 2)
- [x] On final submit: POST + redirect to detail page + toast (REQ-CO-03 Scenario 1)
- [x] Loading: spinner "Creando convocatoria..." + all steps locked (REQ-CO-03 Scenario 6)
- [x] Error: return to step 3 for retry (REQ-CO-03 Scenario 7)

### Task 5.4: Create `ImportarAlumnosUploader` component
- **File**: `frontend/src/features/coordinacion/components/coloquios/ImportarAlumnosUploader.tsx`
- [x] Convocatoria selector + file input (CSV/XLSX) (REQ-CO-02 Scenario 1)
- [x] Client-side file type validation (REQ-CO-02 Scenario 2)
- [x] Upload via FormData (REQ-CO-02 Scenario 1)
- [x] Partial errors: expandable list (REQ-CO-02 Scenario 3)
- [x] Disabled file input when no convocatoria selected (REQ-CO-02 Scenario 4)
- [x] Loading: indeterminate progress bar + "Importando..." (REQ-CO-02 Scenario 5)
- [x] Error: preserved file selection (REQ-CO-02 Scenario 6)

### Task 5.5: Create `ConvocatoriaTable` component
- **File**: `frontend/src/features/coordinacion/components/coloquios/ConvocatoriaTable.tsx`
- [x] Columns: Materia, Instancia, Días disponibles, Convocados, Reservas activas, Cupos libres, Estado, Acciones (REQ-CO-04 Scenario 1)
- [x] Filters: materia, estado (REQ-CO-04 Scenario 2)
- [x] Paginated (REQ-CO-04 Scenario 1)
- [x] Row click: navigate to detail (REQ-CO-04 Scenario 4)
- [x] Empty: "No hay convocatorias de coloquio" + "Crear primera convocatoria" (REQ-CO-04 Scenario 3)
- [x] Loading: skeleton table (REQ-CO-04 Scenario 5)
- [x] Error: message + retry (REQ-CO-04 Scenario 6)

### Task 5.6: Create `ConvocatoriaDetail` component
- **File**: `frontend/src/features/coordinacion/components/coloquios/ConvocatoriaDetail.tsx`
- [x] Detail view with convocatoria info + reservations list (REQ-CO-04 Scenario 4)
- [x] Uses `useConvocatoriaDetail(id)` from `useParams()`
- [x] "Importar alumnos" button triggers ImportarAlumnosUploader inline (REQ-CO-02 Scenario 1)

### Task 5.7: Create `ColoquiosPages.tsx`
- **File**: `frontend/src/features/coordinacion/pages/ColoquiosPages.tsx`
- [x] Sub-route layout with secondary nav: dashboard (metricas + list), nuevo, admin
- [x] Index route renders `<MetricasPanel />` + `<ConvocatoriaTable />` side by side
- [x] Admin sub-route gated by ADMIN permission (TabNav: Convocatorias / Registro académico / Reservas activas) (REQ-CO-05 Scenario 1)
- [x] Detail route uses `useParams()` for convocatoriaId

---

## Phase 6: Tareas

### Task 6.1: Create `hooks/useTareas.ts`
- **File**: `frontend/src/features/coordinacion/hooks/useTareas.ts`
- [x] `useMisTareas(filters?)` — `useQuery<Tarea[]>` key `['coordinacion', 'tareas', 'mis-tareas', filters]`, conditional `refetchInterval` 30s when non-terminal states exist (AD-07)
- [x] `useTareasAdmin(filters?)` — `useQuery<Tarea[]>` key `['coordinacion', 'tareas', 'admin', filters]`, staleTime appropriate for admin view
- [x] `useAsignarTarea()` — `useMutation`, onSuccess invalidates `['coordinacion', 'tareas', 'mis-tareas']` and `['coordinacion', 'tareas', 'admin']`
- [x] `useActualizarEstadoTarea()` — `useMutation`, onSuccess invalidates `['coordinacion', 'tareas']` (broad: all tareas queries)

### Task 6.2: Create `TareaCard` component
- **File**: `frontend/src/features/coordinacion/components/tareas/TareaCard.tsx`
- [x] Card: título, materia, asignador, estado (TareaStatusBadge), fecha creación, fecha límite (REQ-TA-01 Scenario 1)
- [x] Sorted by creation date desc (REQ-TA-01 Scenario 1)
- [x] Inline status change for own tasks (pendiente→en_proceso) with optional comment (REQ-TA-01 Scenario 4)
- [x] "Completar" button expands TareaCommentThread for closure comment (REQ-TA-01 Scenario 5)
- [x] Overdue indicator: red "Vencida" with tooltip (REQ-TA-01 Scenario 9)
- [x] Empty: "No tenés tareas asignadas" + helpful message (REQ-TA-01 Scenario 3)
- [x] Loading: 3 skeleton cards (REQ-TA-01 Scenario 7)
- [x] Error: "Error al cargar tus tareas" + retry (REQ-TA-01 Scenario 8)

### Task 6.3: Create `TareaForm` component
- **File**: `frontend/src/features/coordinacion/components/tareas/TareaForm.tsx`
- [x] Fields: asignado_a (searchable docente selector), materia (optional), título, descripción (textarea), fecha_límite, prioridad (REQ-TA-02 Scenario 1)
- [x] Zod validation: docente + título required (REQ-TA-02 Scenario 2)
- [x] Fecha límite must be future (REQ-TA-02 Scenario 4)
- [x] Docente search after 3+ chars (REQ-TA-02 Scenario 3)
- [x] On success: redirect to `/coordinacion/tareas` + toast (REQ-TA-02 Scenario 1)
- [x] Loading: spinner "Asignando tarea..." + disabled fields (REQ-TA-02 Scenario 5)
- [x] Error: preserved values (REQ-TA-02 Scenario 6)

### Task 6.4: Create `TareaTable` component
- **File**: `frontend/src/features/coordinacion/components/tareas/TareaTable.tsx`
- [x] Columns: Título, Asignado a, Asignador, Materia, Estado, Prioridad, Fecha límite, Creada, Acciones (REQ-TA-03 Scenario 1)
- [x] Filters: docente, asignador, materia, estado, free search (REQ-TA-03 Scenario 1/5)
- [x] Action dropdown: "Aprobar", "Rechazar", "Reasignar" (REQ-TA-03 Scenario 2)
- [x] Reject requires mandatory comment (REQ-TA-03 Scenario 3)
- [x] Empty: "No hay tareas registradas en el sistema" (REQ-TA-03 Scenario 4)
- [x] Loading: skeleton table + disabled filters (REQ-TA-03 Scenario 7)
- [x] Error: message + retry (REQ-TA-03 Scenario 8)

### Task 6.5: Create `TareaCommentThread` component
- **File**: `frontend/src/features/coordinacion/components/tareas/TareaCommentThread.tsx`
- [x] Chronological timeline of comments (REQ-TA-03 Scenario 6)
- [x] New comment input + send button (REQ-TA-03 Scenario 6)
- [x] Expandable/collapsible from TareaCard and TareaTable (REQ-TA-01 Scenario 5)

### Task 6.6: Create `TareaStatusBadge` component
- **File**: `frontend/src/features/coordinacion/components/tareas/TareaStatusBadge.tsx`
- [x] Color map: pendiente=grey, en_proceso=blue, completada=green, aprobada=emerald, rechazada=red
- [x] Inline click-to-change dropdown for own tasks (REQ-TA-01 Scenario 4)

### Task 6.7: Create `TareasPages.tsx`
- **File**: `frontend/src/features/coordinacion/pages/TareasPages.tsx`
- [x] Sub-route layout with secondary nav: mis-tareas, asignar, admin
- [x] Renders `<Outlet />` for each sub-route
- [x] Admin sub-route gated by permission `tareas:admin`

---

## Phase 7: Avisos

### Task 7.1: Create `hooks/useAvisos.ts`
- **File**: `frontend/src/features/coordinacion/hooks/useAvisos.ts`
- [x] `useAvisos(filters?)` — `useQuery<Aviso[]>` key `['coordinacion', 'avisos', 'list', filters]`
- [x] `useCrearAviso()` — `useMutation`, onSuccess invalidates `['coordinacion', 'avisos', 'list']`
- [x] `useEditarAviso()` — `useMutation`, onSuccess invalidates `['coordinacion', 'avisos', 'list']`
- [x] `useEliminarAviso()` — `useMutation`, onSuccess invalidates `['coordinacion', 'avisos', 'list']`
- [x] `useConfirmarAck()` — `useMutation`

### Task 7.2: Create `AvisoForm` component
- **File**: `frontend/src/features/coordinacion/components/avisos/AvisoForm.tsx`
- [x] Fields: título, cuerpo (markdown textarea), alcance condicional (via `AvisoScopeSelector`), roles destinatarios, severidad (informativo/advertencia/crítico), fecha_desde, fecha_hasta, requiere_ack (REQ-AV-01 Scenario 3)
- [x] "Publicar" vs "Guardar borrador" actions (REQ-AV-01 Scenario 3-4)
- [x] Zod validation: cuerpo not empty (REQ-AV-01 Scenario 8), fecha_hasta > fecha_desde (REQ-AV-01 Scenario 7)
- [x] Edit mode: precargado for borrador/publicado (REQ-AV-01 Scenario 5)
- [x] Delete with confirmation dialog (REQ-AV-01 Scenario 6)

### Task 7.3: Create `AvisoScopeSelector` component
- **File**: `frontend/src/features/coordinacion/components/avisos/AvisoScopeSelector.tsx`
- [x] Scope radio: global / materia / cohorte (REQ-AV-02 Scenarios 1-3)
- [x] Materia/cohorte selectors appear conditionally based on scope (REQ-AV-02 Scenarios 2-3)
- [x] Roles destinatarios: checkboxes for TUTOR, PROFESOR, COORDINADOR, ADMIN, FINANZAS, NEXO (REQ-AV-02 Scenario 4)
- [x] Default: all roles selected (REQ-AV-02 Scenario 4)

### Task 7.4: Create `AvisoCard` component
- **File**: `frontend/src/features/coordinacion/components/avisos/AvisoCard.tsx`
- [x] Card: título, severidad badge (info/warning/critical colors), alcance, vigencia, requiere_ack sí/no, estado (REQ-AV-01 Scenario 1)
- [x] Sorted by creation date desc (REQ-AV-01 Scenario 1)
- [x] Filters: estado, severidad, alcance (REQ-AV-01 Scenario 1)
- [x] Empty: "No hay avisos publicados" + "+ Nuevo aviso" (REQ-AV-01 Scenario 2)
- [x] Loading: 3 skeleton cards (REQ-AV-01 Scenario 9)
- [x] Error: message + retry (REQ-AV-01 Scenario 10)
- [x] Ack detail: counter "{N}/{M} destinatarios leyeron" when requiere_ack (REQ-AV-04 Scenario 3)

### Task 7.5: Create `AvisosPages.tsx`
- **File**: `frontend/src/features/coordinacion/pages/AvisosPages.tsx`
- [x] Sub-route layout with secondary nav: list, nuevo
- [x] Renders `<Outlet />` for each sub-route
- [x] Edit route uses `useParams()` for avisoId

---

## Phase 8: Monitor

### Task 8.1: Create `hooks/useMonitorCoordinacion.ts`
- **File**: `frontend/src/features/coordinacion/hooks/useMonitorCoordinacion.ts`
- [x] `useMonitorGeneral(filters, page)` — `useQuery` key `['coordinacion', 'monitor', 'general', filters, page]`, `enabled` with debounce
- [x] `useAuditoria(filters, page)` — `useQuery` key `['coordinacion', 'monitor', 'auditoria', filters, page]`, `enabled` with debounce

### Task 8.2: Create `MonitorFilters` component (shared)
- **File**: `frontend/src/features/coordinacion/components/monitor/MonitorFilters.tsx`
- [x] Filters: nombre, email, comisión, regional, materia, actividad, date range (REQ-MO-01 Scenario 1)
- [x] Free text search `q` (REQ-MO-01 Scenario 1)
- [x] Debounced text inputs at 300ms (REQ-MO-01 Scenario 3)
- [x] Date range validation: fecha_desde < fecha_hasta (REQ-MO-01 Scenario 4)
- [x] "Limpiar filtros" resets all + page to 1 (REQ-MO-01 Scenario 6)
- [x] Emits `onFiltersChange(filters)` to parent

### Task 8.3: Create `MonitorGeneralTable` component
- **File**: `frontend/src/features/coordinacion/components/monitor/MonitorGeneralTable.tsx`
- [x] Columns: Alumno, Email, Comisión, Regional, Materia, Actividad, Estado, Última actividad (REQ-MO-01 Scenario 1)
- [x] Paginated (50 per page) with "Mostrando {from}-{to} de {total}" (REQ-MO-01 Scenario 7)
- [x] Page resets to 1 when filters change (REQ-MO-01 Scenario 8)
- [x] Export CSV button (REQ-MO-01 Scenario 9)
- [x] Empty: "No se encontraron datos de monitoreo para los filtros seleccionados" (REQ-MO-01 Scenario 2)
- [x] Loading: skeleton table + disabled filters (REQ-MO-01 Scenario 10)
- [x] Error: message + "Reintentar", cached data visible (REQ-MO-01 Scenario 11)

### Task 8.4: Create `AuditoriaTable` component
- **File**: `frontend/src/features/coordinacion/components/monitor/AuditoriaTable.tsx`
- [x] Columns: Fecha/Hora, Docente, Rol, Acción, Materia, Registros afectados, IP, User-Agent (REQ-MO-02 Scenario 1)
- [x] Filters: date range, docente, materia, tipo de acción, free search (REQ-MO-02 Scenario 1)
- [x] Paginated (50 per page), sorted by fecha desc (REQ-MO-02 Scenario 1)
- [x] Expandable rows: click shows detail (request payload, response status, duration, full UA) (REQ-MO-02 Scenario 9)
- [x] Export CSV button (REQ-MO-02 Scenario 7)
- [x] Empty: "No hay actividad registrada para los filtros seleccionados" (REQ-MO-02 Scenario 2)
- [x] Loading: skeleton table + disabled filters (REQ-MO-02 Scenario 10)
- [x] Error: message + retry (REQ-MO-02 Scenario 11)

### Task 8.5: Create `MonitorPages.tsx`
- **File**: `frontend/src/features/coordinacion/pages/MonitorPages.tsx`
- [x] Sub-route layout with secondary nav: general, auditoria
- [x] Index route renders `<MonitorFilters />` + `<MonitorGeneralTable />`
- [x] Auditoria route renders shared `<MonitorFilters />` (adapted) + `<AuditoriaTable />`

---

## Phase 9: Final Integration

### Task 9.1: Verify all routes work
- [x] All 7 domain routes mount correctly under `/coordinacion`
- [x] All sub-routes resolve (equipos/usuarios, equipos/asignaciones/masiva, encuentros/:id/editar, etc.)
- [x] No duplicate route paths with existing routes (e.g., old `/equipos` replaced)
- [x] `CoordinacionLayout` renders `<Outlet />` correctly for nested routes
- [x] Deep links work (navigating directly to `/coordinacion/coloquios/123`)

### Task 9.2: Verify permission guards on sidebar nav and routes
- [x] Sidebar "Coordinación" section only visible to users with at least one coordinación permission
- [x] Each sidebar entry gated by its specific permission
- [x] Admin-only sub-routes (equipos/usuarios, coloquios/admin) blocked by `PermissionGuard`
- [x] All domain pages wrapped with appropriate permission guard
- [x] Verify `DashboardHome.tsx` ROUTE_PRIORITY includes entries for coordinación routes

### Task 9.3: Verify mutation → invalidation matrix per design §3
- [x] Equipos: crearAsignacion invalidates `['coordinacion', 'equipos', 'asignaciones']` and `['coordinacion', 'equipos', 'mis-equipos']`
- [x] Equipos: asignacionMasiva, clonarEquipo invalidate `['coordinacion', 'equipos', 'asignaciones']`
- [x] Equipos: actualizarVigencia invalidates `['coordinacion', 'equipos', 'asignaciones']` and `['coordinacion', 'equipos', 'mis-equipos']`
- [x] Equipos: crearEditarUsuario invalidates `['coordinacion', 'equipos', 'usuarios']`
- [x] Estructura: crearCarrera, crearCohorte, subirPrograma, eliminarPrograma, crearEvaluacion — each invalidates its respective key
- [x] Encuentros: crearRecurrente, crearUnico, editarEncuentro invalidate `['coordinacion', 'encuentros', 'list']`
- [x] Encuentros: registrarGuardia invalidates `['coordinacion', 'encuentros', 'guardias']`
- [x] Coloquios: crearConvocatoria invalidates `['coordinacion', 'coloquios', 'list']`
- [x] Coloquios: importarAlumnos invalidates `['coordinacion', 'coloquios', 'metricas']` and `['coordinacion', 'coloquios', 'detail']`
- [x] Coloquios: cerrarConvocatoria invalidates `['coordinacion', 'coloquios', 'list']` and `['coordinacion', 'coloquios', 'admin']`
- [x] Tareas: asignarTarea invalidates `['coordinacion', 'tareas', 'mis-tareas']` and `['coordinacion', 'tareas', 'admin']`
- [x] Tareas: actualizarEstadoTarea invalidates `['coordinacion', 'tareas']` (broad)
- [x] Avisos: crearAviso, editarAviso, eliminarAviso invalidate `['coordinacion', 'avisos', 'list']`

### Task 9.4: Verify all loading/empty/error states across all domains
- [x] **Equipos**: EquipoCard skeleton → "No tenés equipos asignados" → error + retry
- [x] **Equipos usaurios**: UsuarioTable skeleton → empty → error + retry
- [x] **Equipos asignaciones**: EquipoTable skeleton → "No hay asignaciones" → error + retry
- [x] **Estructura carreras**: CarreraForm skeleton → "No hay carreras" → error
- [x] **Estructura cohortes**: CohorteForm skeleton → "No hay cohortes" → error
- [x] **Estructura programas**: ProgramaUploader skeleton → "No hay programas" → upload error
- [x] **Estructura evaluaciones**: EvaluacionForm skeleton → "No hay evaluaciones" → error
- [x] **Encuentros**: EncuentroTable skeleton → "No hay encuentros" → error + retry
- [x] **Encuentros guardias**: GuardiaTable skeleton → "No hay guardias" → error
- [x] **Coloquios**: MetricasPanel skeleton → zero state → error + retry
- [x] **Coloquios convocatorias**: ConvocatoriaTable skeleton → "No hay convocatorias" + create button → error
- [x] **Tareas**: TareaCard skeleton → "No tenés tareas" → error
- [x] **Tareas admin**: TareaTable skeleton → "No hay tareas" → error
- [x] **Avisos**: AvisoCard skeleton → "No hay avisos" + nuevo button → error
- [x] **Monitor**: MonitorGeneralTable skeleton + disabled filters → empty → error + cached data
- [x] **Monitor auditoría**: AuditoriaTable skeleton + disabled filters → empty → error

### Task 9.5: Cross-domain integration checks
- [x] "Ir a estructura" button from MisEquipos empty state navigates correctly (REQ-EQ-01 Scenario 2)
- [x] Cohorte selector populated in ClonarEquipoForm uses estructura/cohortes
- [x] Materia selector across domains uses consistent data source
- [x] Task polling stops when all tasks reach terminal states (AD-07)
- [x] Recurrent encuentro generation shows proper progress feedback (AD-06)
- [x] CSV exports download via Axios blob with correct filename

---

## Summary

| Phase | Tasks | Focus |
|-------|-------|-------|
| 1 Foundation | 18 | Types, services, routes, layout, sidebar |
| 2 Equipos | 11 | Team management (cards, tables, forms) |
| 3 Estructura | 6 | Academic structure (carreras, cohortes, programas, evaluaciones) |
| 4 Encuentros | 8 | Encounters (recurrent, single, guardias) |
| 5 Coloquios | 7 | Colloquia (metrics, wizard, admin) |
| 6 Tareas | 7 | Task workflow (cards, forms, comments) |
| 7 Avisos | 5 | Announcements (form, scope selector, cards) |
| 8 Monitor | 5 | Monitoring (general table, auditoria, filters) |
| 9 Integration | 5 | Wiring, permissions, invalidation, state checks |
| **Total** | **72** | |

### Implementation Order
1. **Phase 1 (Foundation)** — types, services, routes, layout, sidebar — MUST go first
2. **Phase 2 (Equipos)** — highest usage, core to semester setup flow (FL-03)
3. **Phase 3 (Estructura)** — needed by equipos clonar and encuentros selectors
4. **Phase 4 (Encuentros)** — second highest priority, needs materia/cohorte selectors from estructura
5. **Phase 5 (Coloquios)** — complex wizard, start early but integrate after foundation is solid
6. **Phase 6 (Tareas)** — self-contained workflow, can parallel with Phase 5
7. **Phase 7 (Avisos)** — self-contained, lowest complexity
8. **Phase 8 (Monitor)** — uses shared filters, can be built in parallel with Phases 6-7
9. **Phase 9 (Integration)** — verify everything works together end-to-end

Phases 6, 7, and 8 can be built in parallel (no cross-dependencies between tareas, avisos, and monitor).
