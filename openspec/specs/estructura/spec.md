# Estructura Académica — Spec

> ABM de carreras, ABM de cohortes, programas de materias (upload de documentos) y fechas de evaluaciones con vista calendario.

---

## REQ-ES-01: ABM carreras

El componente `CarreraForm` + tabla permite al ADMIN crear, editar y cambiar estado (activa/inactiva) de carreras, consumiendo `GET /api/v1/estructura/carreras`, `POST /api/v1/estructura/carreras` y `PUT /api/v1/estructura/carreras/{id}`.

### Scenarios

**Scenario 1: Listado de carreras**
GIVEN el usuario autenticado tiene permiso `estructura:gestionar`
WHEN navega a `/coordinacion/estructura/carreras`
THEN se muestra una tabla paginada con columnas: Código, Nombre, Estado (activa/inactiva), Creada
AND un botón "+ Nueva carrera" está visible arriba a la derecha

**Scenario 2: Crear carrera exitosa**
GIVEN el listado de carreras está visible
WHEN el usuario hace clic en "+ Nueva carrera"
THEN `CarreraForm` muestra campos: código (texto corto, ej: "LIC-MAT"), nombre (texto largo)
WHEN completa y envía
THEN `POST /api/v1/estructura/carreras` se llama con `{ codigo, nombre }`
AND en 201, la tabla se actualiza
AND un toast "Carrera creada correctamente" se muestra

**Scenario 3: Crear carrera — código duplicado**
GIVEN el formulario de creación
WHEN el usuario ingresa un código ya existente
THEN `POST /api/v1/estructura/carreras` retorna 409
AND se muestra "El código ya está registrado" inline en el campo código

**Scenario 4: Editar carrera**
GIVEN la tabla de carreras
WHEN el usuario hace clic en editar
THEN `CarreraForm` se abre precargado
WHEN modifica el nombre y guarda
THEN `PUT /api/v1/estructura/carreras/{id}` se llama
AND la tabla se actualiza

**Scenario 5: Cambiar estado de carrera (con confirmación)**
GIVEN la tabla de carreras
WHEN el usuario hace clic en el toggle de estado
THEN un diálogo de confirmación aparece: "¿Cambiar estado de {nombre}?"
WHEN confirma
THEN `PUT /api/v1/estructura/carreras/{id}` se llama con `{ activa: false }`
AND el estado se actualiza en la tabla

**Scenario 6: Listado vacío**
GIVEN no hay carreras creadas
WHEN el usuario navega a la sección
THEN se muestra "No hay carreras registradas"
AND un botón "+ Nueva carrera" está visible

**Scenario 7: Loading state**
GIVEN el componente monta
WHILE los datos cargan
THEN una tabla esqueleto con 3 filas placeholder se muestra

**Scenario 8: Error state**
GIVEN el listado
WHEN `GET /api/v1/estructura/carreras` falla
THEN se muestra "Error al cargar carreras" con botón "Reintentar"

**Scenario 9: Validación Zod — campos requeridos**
GIVEN el formulario de carrera
WHEN el usuario intenta enviar con código vacío o nombre vacío
THEN los mensajes de validación aparecen debajo de cada campo
AND el envío se bloquea

---

## REQ-ES-02: ABM cohortes

El componente `CohorteForm` + tabla permite al ADMIN crear, editar y cambiar estado de cohortes, consumiendo `GET /api/v1/estructura/cohortes`, `POST /api/v1/estructura/cohortes` y `PUT /api/v1/estructura/cohortes/{id}`.

### Scenarios

**Scenario 1: Listado de cohortes**
GIVEN el usuario tiene permiso `estructura:gestionar`
WHEN navega a `/coordinacion/estructura/cohortes`
THEN se muestra una tabla con columnas: Nombre (ej: "MAR-2025"), Año, Vigencia desde, Vigencia hasta, Estado
AND filtros por año y estado están disponibles
AND un botón "+ Nueva cohorte"

**Scenario 2: Crear cohorte exitosa**
GIVEN el listado de cohortes
WHEN el usuario hace clic en "+ Nueva cohorte"
THEN `CohorteForm` muestra campos: nombre, año, fecha_desde, fecha_hasta, estado
WHEN completa y envía
THEN `POST /api/v1/estructura/cohortes` se llama
AND en 201, la tabla se actualiza

**Scenario 3: Crear cohorte — nombre duplicado (mismo año)**
GIVEN el formulario
WHEN el usuario ingresa un nombre de cohorte ya existente para el mismo año
THEN `POST` retorna 409
AND se muestra "Ya existe una cohorte con ese nombre para el año seleccionado"

**Scenario 4: Editar cohorte**
GIVEN la tabla de cohortes
WHEN el usuario hace clic en editar
THEN `CohorteForm` se abre precargado
WHEN modifica la vigencia y guarda
THEN `PUT /api/v1/estructura/cohortes/{id}` se llama

**Scenario 5: Listado vacío**
GIVEN no hay cohortes
WHEN el usuario navega
THEN se muestra "No hay cohortes registradas"

**Scenario 6: Filtro por año**
GIVEN hay múltiples cohortes
WHEN el usuario selecciona un año en el filtro
THEN la tabla se filtra solo a cohortes de ese año
AND la query incluye `?year=...`

**Scenario 7: Loading state**
GIVEN el componente monta
WHILE los datos cargan
THEN tabla esqueleto se muestra

**Scenario 8: Error state**
GIVEN el listado
WHEN la API falla
THEN se muestra mensaje de error con reintento

---

## REQ-ES-03: Programas de materias (upload)

El componente `ProgramaUploader` permite subir y asociar el programa oficial (documento) de cada materia para una combinación de carrera×cohorte, consumiendo `GET /api/v1/estructura/programas` y `POST /api/v1/estructura/programas`.

### Scenarios

**Scenario 1: Subir programa exitoso**
GIVEN el usuario tiene permiso `estructura:gestionar`
WHEN navega a `/coordinacion/estructura/programas`
THEN se muestra un formulario con: materia (dropdown), carrera, cohorte, título descriptivo, file input (PDF/DOC/DOCX)
WHEN selecciona materia="Matemática", carrera="LIC-MAT", cohorte="MAR-2025", escribe título "Programa 2025"
AND selecciona un archivo PDF
AND hace clic en "Subir programa"
THEN `POST /api/v1/estructura/programas` se llama con FormData conteniendo el archivo + metadata
AND en 201, se muestra "Programa subido correctamente"
AND el listado de programas se actualiza

**Scenario 2: Tipo de archivo inválido**
GIVEN el file input está visible
WHEN el usuario selecciona un archivo .exe o .zip
THEN validación client-side muestra "Formato no soportado. Usá PDF, DOC o DOCX"
AND el envío se bloquea

**Scenario 3: Archivo muy grande**
GIVEN el usuario selecciona un archivo
WHEN el backend retorna 413 o un error de tamaño máximo
THEN se muestra "El archivo supera el tamaño máximo permitido"

**Scenario 4: Listado de programas existentes**
GIVEN hay programas subidos previamente
WHEN el usuario accede a la sección
THEN debajo del uploader se muestra una tabla con columnas: Materia, Carrera, Cohorte, Título, Fecha de subida, Acciones (descargar, eliminar)

**Scenario 5: Descargar programa**
GIVEN la tabla de programas
WHEN el usuario hace clic en "Descargar" de una fila
THEN `GET /api/v1/estructura/programas/{id}/download` se ejecuta
AND el archivo se descarga con el nombre original

**Scenario 6: Eliminar programa con confirmación**
GIVEN la tabla de programas
WHEN el usuario hace clic en eliminar
THEN un diálogo de confirmación aparece: "¿Eliminar programa {título}?"
WHEN confirma
THEN `DELETE /api/v1/estructura/programas/{id}` se llama (soft delete)
AND la tabla se actualiza

**Scenario 7: Listado vacío**
GIVEN no hay programas subidos
WHEN el usuario navega
THEN se muestra "No hay programas registrados para ninguna materia"

**Scenario 8: Loading state en subida**
GIVEN el usuario inició la subida
WHILE el POST se procesa
THEN una barra de progreso indeterminada se muestra
AND el botón muestra "Subiendo..."
AND todos los inputs están deshabilitados

**Scenario 9: Error de red en subida**
GIVEN la subida falla
THEN se muestra "Error al subir el programa. Verificá e intentá de nuevo."
AND el formulario conserva los valores

---

## REQ-ES-04: Fechas de evaluaciones

Los componentes `EvaluacionForm` + `EvaluacionCalendar` permiten registrar y visualizar fechas de evaluaciones (parciales, TP, coloquios) por materia × cohorte, consumiendo `GET /api/v1/estructura/evaluaciones`, `POST /api/v1/estructura/evaluaciones` y `PUT /api/v1/estructura/evaluaciones/{id}`.

### Scenarios

**Scenario 1: Vista de evaluaciones con calendario**
GIVEN el usuario tiene permiso `estructura:gestionar`
WHEN navega a `/coordinacion/estructura/evaluaciones`
THEN se muestran dos vistas seleccionables: "Lista" y "Calendario"
AND la vista por defecto es "Lista"
AND arriba hay filtros por materia, cohorte y tipo de evaluación

**Scenario 2: Vista lista con evaluaciones**
GIVEN existen evaluaciones registradas
WHEN el usuario selecciona materia="Matemática" y cohorte="MAR-2025"
THEN la tabla muestra: Materia, Tipo (Parcial/TP/Coloquio), Instancia (1, 2, etc.), Fecha, Cohorte, Título, Acciones (editar, eliminar)

**Scenario 3: Vista calendario**
GIVEN el usuario cambia a la vista "Calendario"
THEN los filtros se mantienen
AND se muestra un calendario mensual con marcadores en las fechas que tienen evaluaciones
AND al hacer clic en una fecha con evaluación se muestra un tooltip con el detalle

**Scenario 4: Crear evaluación exitosa**
GIVEN la vista de evaluaciones
WHEN el usuario hace clic en "+ Nueva evaluación"
THEN `EvaluacionForm` muestra campos: materia, cohorte, tipo (select: Parcial/TP/Coloquio), instancia (número), fecha (datepicker), título
WHEN completa y envía
THEN `POST /api/v1/estructura/evaluaciones` se llama
AND en 201, la tabla/calendario se actualiza

**Scenario 5: Crear evaluación — fecha en el pasado sin confirmación**
GIVEN el formulario
WHEN el usuario selecciona una fecha pasada
THEN una advertencia aparece: "La fecha seleccionada ya pasó. ¿Confirmar de todas formas?"
AND el envío requiere confirmación adicional

**Scenario 6: Editar evaluación**
GIVEN la tabla de evaluaciones
WHEN el usuario edita una evaluación
THEN `EvaluacionForm` se abre precargado
WHEN cambia la fecha y guarda
THEN `PUT /api/v1/estructura/evaluaciones/{id}` se llama

**Scenario 7: Evaluación duplicada (misma materia×cohorte×tipo×instancia)**
GIVEN el formulario de creación
WHEN el usuario intenta crear una evaluación que ya existe para esa materia, cohorte, tipo e instancia
THEN `POST` retorna 409
AND se muestra "Ya existe una evaluación de {tipo} instancia {N} para esta materia y cohorte"

**Scenario 8: Generar contenido para aula virtual**
GIVEN la tabla de evaluaciones con filtros aplicados
WHEN el usuario hace clic en "Generar contenido LMS"
THEN `GET /api/v1/encuentros/contenido-aula?materia_id=X&cohorte_id=Y` se llama (o un endpoint específico de evaluaciones)
AND se muestra un preview del contenido formateado listo para copiar
AND un botón "Copiar al portapapeles" está disponible

**Scenario 9: Listado vacío**
GIVEN no hay evaluaciones para los filtros seleccionados
WHEN el usuario navega
THEN se muestra "No hay evaluaciones registradas para los filtros seleccionados"

**Scenario 10: Loading state**
GIVEN el componente monta
WHILE los datos cargan
THEN skeleton de tabla o calendario placeholder se muestra

**Scenario 11: Error state**
GIVEN la API falla
THEN se muestra "Error al cargar evaluaciones" con reintento

---

## REQ-ES-05: Admin — ABM Carreras (Frontend Admin)

El componente `CarreraTable` + `CarreraForm` en el módulo admin permite al ADMIN crear, editar y toggle estado de carreras consumiendo `/api/admin/carreras`.

### Scenarios

**Scenario 1: Crear carrera**
GIVEN un usuario ADMIN
WHEN agrega una Carrera
THEN aparece en la lista

**Scenario 2: Toggle estado**
GIVEN una Carrera existente
WHEN el estado se togglea
THEN la lista se actualiza

---

## REQ-ES-06: Admin — ABM Cohortes (Frontend Admin)

El componente `CohorteTable` + `CohorteForm` en el módulo admin permite al ADMIN crear, editar y toggle estado de cohortes con año y vigencia.

### Scenarios

**Scenario 1: Crear cohorte**
GIVEN un usuario ADMIN
WHEN agrega una Cohorte
THEN aparece en el tab Cohortes

---

## REQ-ES-07: Admin — ABM Materias (Frontend Admin)

El componente `MateriaTable` + `MateriaForm` en el módulo admin permite al ADMIN crear, editar y toggle estado de materias.

### Scenarios

**Scenario 1: Crear materia**
GIVEN un usuario ADMIN
WHEN agrega una Materia
THEN aparece en el tab Materias

---

## REQ-ES-08: Admin — Filtros de estructura (Frontend Admin)

El módulo admin SHALL filtrar carreras, cohortes y materias por nombre y estado.

### Scenarios

**Scenario 1: Búsqueda por nombre**
GIVEN un catálogo con items
WHEN el usuario busca por nombre
THEN solo los items que coinciden se muestran
