# Coloquios — Spec

> Panel de métricas, importación de alumnos, creación y listado de convocatorias, y administración global de coloquios.

---

## REQ-CO-01: Panel de métricas de coloquios

El componente `MetricasPanel` muestra KPIs del estado de coloquios, consumiendo `GET /api/v1/coloquios/metricas`.

### Scenarios

**Scenario 1: Panel con métricas**
GIVEN el usuario tiene permiso `coloquios:ver`
WHEN navega a `/coordinacion/coloquios`
THEN la página inicia mostrando el `MetricasPanel` con 4 KPI cards: Total alumnos cargados, Instancias activas, Reservas activas, Notas registradas
AND debajo se muestra la tabla de convocatorias (`ConvocatoriaTable`)

**Scenario 2: Todas las métricas en cero**
GIVEN no hay coloquios configurados
WHEN el panel carga
THEN cada KPI card muestra "0"
AND los iconos se muestran en gris (sin actividad)

**Scenario 3: Loading state**
GIVEN el componente monta
WHILE `GET /api/v1/coloquios/metricas` se procesa
THEN 4 skeleton cards con shimmer se muestran

**Scenario 4: Error state**
GIVEN la API de métricas falla
THEN las KPI cards muestran "—" en lugar del valor
AND un mensaje "Error al cargar métricas" aparece en la parte superior del panel
AND un botón "Reintentar" está visible

**Scenario 5: Refresco periódico**
GIVEN el panel está visible
WHEN el usuario hace clic en "Actualizar"
THEN todas las métricas se recargan desde la API

---

## REQ-CO-02: Importar alumnos a una convocatoria

El componente `ImportarAlumnosUploader` permite cargar el padrón de alumnos habilitados para una convocatoria, consumiendo `POST /api/v1/coloquios/importar-alumnos`.

### Scenarios

**Scenario 1: Importar alumnos exitoso**
GIVEN el usuario está en la página de detalle de una convocatoria o en la sección de importación
WHEN navega a `/coordinacion/coloquios` y selecciona "Importar alumnos" de una convocatoria
THEN se muestra un formulario: selector de convocatoria, file input (CSV/XLSX)
WHEN selecciona un archivo válido y hace clic en "Importar"
THEN `POST /api/v1/coloquios/importar-alumnos` se llama con FormData
AND en 200, se muestra " {N} alumnos importados correctamente"
AND las queries de métricas y convocatorias se invalidan

**Scenario 2: Archivo con formato inválido**
GIVEN el file input está visible
WHEN el usuario selecciona un archivo .pdf
THEN validación client-side muestra "Formato no soportado. Usá CSV o XLSX"
AND el envío se bloquea

**Scenario 3: Importación con errores parciales**
GIVEN el archivo fue enviado
WHEN el backend retorna 200 con `{ imported_count: 45, errors: [{ row: 12, message: "DNI duplicado" }] }`
THEN se muestra "45 alumnos importados. 1 error."
AND los errores se listan en una sección expandible

**Scenario 4: Sin convocatoria seleccionada**
GIVEN el formulario de importación
WHEN no hay una convocatoria seleccionada
THEN el file input está deshabilitado
AND se muestra "Seleccioná una convocatoria primero"

**Scenario 5: Loading state**
GIVEN el usuario inició la importación
WHILE el POST se procesa
THEN una barra de progreso indeterminada se muestra
AND el botón muestra "Importando..."

**Scenario 6: Error state**
GIVEN la importación falla
THEN se muestra "Error al importar alumnos" con el mensaje del backend
AND el formulario conserva el archivo seleccionado

---

## REQ-CO-03: Crear convocatoria de coloquio

El componente `ConvocatoriaForm` permite crear una nueva convocatoria con wizard multi-paso, consumiendo `POST /api/v1/coloquios`.

### Scenarios

**Scenario 1: Crear convocatoria exitosa (wizard completo)**
GIVEN el usuario tiene permiso `coloquios:crear`
WHEN navega a `/coordinacion/coloquios/nuevo`
THEN el wizard muestra 3 pasos:
  Paso 1 — "Datos generales": materia, cohorte, instancia (número), título
  Paso 2 — "Días y cupos": selector de días con fecha y cupo máximo por día (se pueden agregar múltiples días)
  Paso 3 — "Confirmar": resumen de todos los datos
WHEN completa el paso 1 y hace clic en "Siguiente"
THEN se valida y pasa al paso 2
WHEN agrega 3 días con cupos y hace clic en "Siguiente"
THEN se valida y pasa al paso 3
WHEN revisa el resumen y hace clic en "Confirmar"
THEN `POST /api/v1/coloquios` se llama con todos los datos
AND en 201, se redirige a `/coordinacion/coloquios/{id}`
AND un toast "Convocatoria creada correctamente" se muestra

**Scenario 2: Navegación backward en wizard**
GIVEN el usuario está en el paso 2 del wizard
WHEN hace clic en "Anterior"
THEN vuelve al paso 1 con los datos previamente ingresados intactos

**Scenario 3: Validación — paso 1 incompleto**
GIVEN el paso 1 del wizard
WHEN el usuario intenta avanzar sin completar materia o instancia
THEN validación Zod muestra errores en los campos faltantes
AND no se avanza al paso 2

**Scenario 4: Validación — paso 2 sin días agregados**
GIVEN el paso 2 del wizard
WHEN el usuario intenta avanzar sin agregar ningún día
THEN se muestra "Agregá al menos un día con cupos"
AND no se avanza al paso 3

**Scenario 5: Cupo máximo inválido**
GIVEN el paso 2 del wizard
WHEN el usuario ingresa cupo 0 o negativo para un día
THEN validación Zod muestra "El cupo debe ser al menos 1"
AND el botón "Agregar día" permanece deshabilitado

**Scenario 6: Loading state en confirmación**
GIVEN el usuario hizo clic en "Confirmar"
WHILE el POST se procesa
THEN el botón muestra spinner con "Creando convocatoria..."
AND todos los pasos se bloquean

**Scenario 7: Error state**
GIVEN el POST falla
THEN se muestra "Error al crear la convocatoria"
AND el wizard vuelve al paso 3 para reintento

---

## REQ-CO-04: Listado de convocatorias

El componente `ConvocatoriaTable` muestra todas las convocatorias con métricas operativas, consumiendo `GET /api/v1/coloquios`.

### Scenarios

**Scenario 1: Listado con convocatorias activas**
GIVEN el usuario tiene permiso `coloquios:ver`
WHEN navega a `/coordinacion/coloquios`
THEN debajo del panel de métricas se muestra la tabla con columnas: Materia, Instancia, Días disponibles, Convocados, Reservas activas, Cupos libres, Estado, Acciones
AND la tabla está paginada

**Scenario 2: Filtros en listado**
GIVEN la tabla está visible
WHEN el usuario filtra por materia o estado
THEN la query incluye los parámetros de filtro
AND la tabla se actualiza

**Scenario 3: Sin convocatorias**
GIVEN no hay convocatorias creadas
WHEN el usuario navega
THEN se muestra "No hay convocatorias de coloquio"
AND un botón "Crear primera convocatoria" navega a `/coordinacion/coloquios/nuevo`

**Scenario 4: Navegar al detalle**
GIVEN la tabla de convocatorias
WHEN el usuario hace clic en una fila
THEN navega a `/coordinacion/coloquios/{convocatoriaId}`
AND se muestra la página de detalle con la información de la convocatoria y sus reservas

**Scenario 5: Loading state**
GIVEN el componente monta
WHILE los datos cargan
THEN tabla esqueleto se muestra

**Scenario 6: Error state**
GIVEN la API falla
THEN se muestra "Error al cargar convocatorias" con reintento

---

## REQ-CO-05: Administración global de coloquios (ADMIN)

El componente `ColoquiosAdmin` permite al ADMIN gestionar todas las convocatorias y el registro académico consolidado, consumiendo `GET /api/v1/coloquios/admin` y `PUT /api/v1/coloquios/admin`.

### Scenarios

**Scenario 1: Vista de admin global**
GIVEN el usuario tiene rol ADMIN
WHEN navega a `/coordinacion/coloquios/admin`
THEN se muestran tres sub-secciones en tabs: "Convocatorias", "Registro académico", "Reservas activas"
AND la tab "Convocatorias" está seleccionada por defecto

**Scenario 2: Gestión de convocatorias (admin)**
GIVEN la tab "Convocatorias" está activa
THEN se muestra una tabla con todas las convocatorias del tenant (activas y cerradas)
AND cada fila tiene acciones: editar, cerrar, eliminar

**Scenario 3: Cerrar convocatoria con confirmación**
GIVEN la tabla de admin
WHEN el ADMIN hace clic en "Cerrar" de una convocatoria activa
THEN un diálogo de confirmación muestra "¿Cerrar la convocatoria {título}? Los alumnos no podrán reservar."
WHEN confirma
THEN `PUT /api/v1/coloquios/admin/{id}` se llama con `{ estado: "cerrada" }`
AND la tabla se actualiza

**Scenario 4: Registro académico consolidado**
GIVEN la tab "Registro académico" está activa
THEN se muestra una tabla con resultados de coloquios: Alumno, Materia, Fecha, Nota, Estado
AND filtros disponibles: materia, cohorte, rango de fechas
AND un botón "Exportar CSV" permite descargar los resultados

**Scenario 5: Reservas activas**
GIVEN la tab "Reservas activas" está activa
THEN se muestra una tabla con todas las reservas activas: Alumno, Convocatoria, Día, Horario, Estado
AND un botón "Liberar reserva" permite cancelar una reserva individual

**Scenario 6: Acción denegada (no ADMIN)**
GIVEN el usuario tiene rol COORDINADOR pero no ADMIN
WHEN intenta navegar a `/coordinacion/coloquios/admin`
THEN `PermissionGuard` muestra 403
AND la entrada de navegación "Admin" no se renderiza en el sidebar de coloquios

**Scenario 7: Loading state**
GIVEN el ADMIN navega a la sección
WHILE los datos cargan
THEN skeleton de tabs con placeholders se muestra

**Scenario 8: Error state**
GIVEN la API falla
THEN se muestra "Error al cargar datos de administración" con reintento
