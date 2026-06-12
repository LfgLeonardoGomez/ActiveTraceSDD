# Encuentros y Disponibilidad — Spec

> Creación de encuentros recurrentes y únicos, edición de instancias, generación de contenido para aula virtual, vista transversal de coordinación y registro de guardias.

---

## REQ-EN-01: Crear encuentro recurrente

El componente `EncuentroRecurrenteForm` permite definir un slot semanal que genera instancias automáticas, consumiendo `POST /api/v1/encuentros/recurrente`.

### Scenarios

**Scenario 1: Crear serie recurrente exitosa**
GIVEN el usuario tiene permiso `encuentros:crear`
WHEN navega a `/coordinacion/encuentros/recurrente`
THEN el formulario muestra campos: materia (dropdown), día de la semana (lunes a viernes), horario (time picker), fecha de inicio (datepicker), cantidad de semanas (number input, 1-16), título, enlace de videoconferencia
WHEN completa y envía
THEN `POST /api/v1/encuentros/recurrente` se llama con los datos
AND en 200, se muestra "Serie creada correctamente — {N} instancias generadas"
AND las queries de encuentros se invalidan

**Scenario 2: Validación — cantidad de semanas fuera de rango**
GIVEN el formulario recurrente
WHEN el usuario ingresa 0 o más de 16 semanas
THEN validación Zod muestra "La cantidad de semanas debe ser entre 1 y 16"
AND el envío se bloquea

**Scenario 3: Validación — fecha de inicio en el pasado**
GIVEN el formulario
WHEN el usuario selecciona una fecha de inicio anterior a hoy
THEN una advertencia muestra "La fecha de inicio ya pasó. Las instancias pasadas no se generarán."
AND el envío requiere confirmación

**Scenario 4: Enlace inválido**
GIVEN el campo de enlace de videoconferencia
WHEN el usuario ingresa un texto que no es una URL válida
THEN validación Zod muestra "Ingresá una URL válida"
AND el envío se bloquea

**Scenario 5: Progreso durante generación**
GIVEN el usuario envió el formulario
WHILE el backend genera las instancias
THEN un spinner con "Generando instancias..." se muestra
AND si la generación tarda >2s, se activa polling con `refetchInterval` para monitorear el progreso

**Scenario 6: Error state**
GIVEN el POST falla
THEN se muestra "Error al crear la serie recurrente" con el mensaje del backend
AND el formulario conserva los valores

---

## REQ-EN-02: Crear encuentro único

El componente `EncuentroForm` permite crear una instancia de encuentro para una fecha y hora específicas, consumiendo `POST /api/v1/encuentros`.

### Scenarios

**Scenario 1: Crear encuentro único exitoso**
GIVEN el usuario tiene permiso `encuentros:crear`
WHEN navega a `/coordinacion/encuentros/nuevo`
THEN el formulario muestra campos: materia, fecha (datepicker), hora (time picker), título, enlace de videoconferencia
WHEN completa y envía
THEN `POST /api/v1/encuentros` se llama
AND en 201, se redirige a `/coordinacion/encuentros` con toast "Encuentro creado correctamente"

**Scenario 2: Validación — fecha y hora requeridas**
GIVEN el formulario
WHEN el usuario intenta enviar sin fecha u hora
THEN validación Zod muestra los errores correspondientes
AND el envío se bloquea

**Scenario 3: Encuentro en el pasado**
GIVEN el formulario
WHEN el usuario selecciona una fecha pasada
THEN una advertencia no bloqueante muestra "El encuentro se registrará con fecha pasada"

**Scenario 4: Error state**
GIVEN el POST falla
THEN se muestra "Error al crear el encuentro" con mensaje del backend

---

## REQ-EN-03: Editar instancia de encuentro

El componente `EncuentroEditModal` permite modificar una instancia existente, consumiendo `PUT /api/v1/encuentros/{id}`.

### Scenarios

**Scenario 1: Editar instancia individual exitosa**
GIVEN el usuario está en la vista transversal de encuentros
WHEN hace clic en el ícono de editar de una instancia
THEN `EncuentroEditModal` se abre con campos precargados: estado (select: programado/realizado/cancelado), enlace de videoconferencia, enlace de grabación, comentario interno
WHEN cambia estado a "realizado" y agrega enlace de grabación
AND hace clic en "Guardar"
THEN `PUT /api/v1/encuentros/{id}` se llama
AND en 200, el modal se cierra
AND la tabla se actualiza
AND un toast "Encuentro actualizado" se muestra

**Scenario 2: Editar instancia de serie recurrente — opción "editar todas las futuras"**
GIVEN la instancia pertenece a una serie recurrente
WHEN el usuario abre el modal de edición
THEN además de los campos, se muestra un checkbox: "Aplicar cambios a todas las instancias futuras de esta serie"
WHEN el usuario marca el checkbox y guarda
THEN `PUT /api/v1/encuentros/{id}` se llama con `{ aplicar_a_futuras: true }`
AND el backend actualiza todas las instancias futuras de la serie

**Scenario 3: Validación — enlace de grabación solo si estado es "realizado"**
GIVEN el modal de edición
WHEN el usuario intenta agregar un enlace de grabación con estado "programado" o "cancelado"
THEN el campo "Enlace de grabación" está deshabilitado
AND un tooltip explica "Disponible solo para encuentros realizados"

**Scenario 4: Error state**
GIVEN el PUT falla
THEN se muestra "Error al actualizar el encuentro"
AND el modal permanece abierto

**Scenario 5: Cancelar encuentro con confirmación**
GIVEN el modal de edición
WHEN el usuario selecciona estado "cancelado"
THEN un diálogo de confirmación muestra "¿Cancelar este encuentro?"
WHEN confirma
THEN el PUT se ejecuta con `{ estado: "cancelado" }`

---

## REQ-EN-04: Generar contenido para aula virtual

El componente `ContenidoAulaPreview` permite generar y copiar contenido formateado con los encuentros programados, consumiendo `GET /api/v1/encuentros/contenido-aula`.

### Scenarios

**Scenario 1: Generar contenido exitoso**
GIVEN el usuario está en cualquier vista de encuentros
WHEN hace clic en "Generar contenido aula virtual"
THEN se muestra un modal con filtros: materia, cohorte, rango de fechas
WHEN selecciona los filtros y hace clic en "Generar"
THEN `GET /api/v1/encuentros/contenido-aula?materia_id=X&cohorte_id=Y&fecha_desde=...&fecha_hasta=...` se llama
AND en 200, se muestra un preview del contenido formateado (tabla con fechas, horarios, títulos, enlaces)

**Scenario 2: Copiar al portapapeles**
GIVEN el contenido generado está visible
WHEN el usuario hace clic en "Copiar al portapapeles"
THEN el contenido se copia al clipboard
AND un toast "Contenido copiado" se muestra

**Scenario 3: Sin encuentros en el rango**
GIVEN el usuario selecciona filtros
WHEN el backend retorna un array vacío
THEN se muestra "No hay encuentros programados en el período seleccionado"

**Scenario 4: Loading state**
GIVEN el usuario hizo clic en "Generar"
WHILE la request está en vuelo
THEN un spinner se muestra en el área de preview
AND el botón "Generar" se deshabilita

**Scenario 5: Error state**
GIVEN la API falla
THEN se muestra "Error al generar el contenido"
AND el modal permanece abierto para reintento

---

## REQ-EN-05: Vista transversal de encuentros (coordinación/admin)

El componente `EncuentroTable` muestra todos los encuentros del tenant con filtros globales, consumiendo `GET /api/v1/encuentros`.

### Scenarios

**Scenario 1: Vista transversal con datos**
GIVEN el usuario tiene rol COORDINADOR o ADMIN
WHEN navega a `/coordinacion/encuentros`
THEN se muestra una tabla con columnas: Materia, Cohorte, Docente, Fecha, Hora, Título, Estado (programado/realizado/cancelado), Enlace, Acciones
AND los filtros disponibles son: materia, cohorte, docente, estado, rango de fechas
AND la tabla está paginada (50 por página)

**Scenario 2: Filtro por estado**
GIVEN la tabla está visible
WHEN el usuario selecciona "Cancelado" en el filtro de estado
THEN la query incluye `?estado=cancelado`
AND la tabla se actualiza

**Scenario 3: Filtro por rango de fechas**
GIVEN la tabla está visible
WHEN el usuario establece "Desde: 2025-03-01" y "Hasta: 2025-03-31"
THEN la query incluye `?fecha_desde=2025-03-01&fecha_hasta=2025-03-31`

**Scenario 4: Sin encuentros**
GIVEN no hay encuentros registrados
WHEN el usuario navega
THEN se muestra "No hay encuentros programados"
AND los filtros aparecen pero sin datos

**Scenario 5: Loading state**
GIVEN el componente monta
WHILE los datos cargan
THEN una tabla esqueleto con 5 filas placeholder se muestra

**Scenario 6: Error state**
GIVEN la API falla
THEN se muestra "Error al cargar encuentros" con botón "Reintentar"

**Scenario 7: Navegar a editar desde la transversal**
GIVEN la tabla de encuentros
WHEN el usuario hace clic en editar de una instancia
THEN navega a `/coordinacion/encuentros/{id}/editar`
AND el modal de edición abre precargado

---

## REQ-EN-06: Registro y consulta de guardias

El componente `GuardiaTable` permite consultar y registrar guardias, consumiendo `GET /api/v1/encuentros/guardias` y `POST /api/v1/encuentros/guardias`.

### Scenarios

**Scenario 1: Vista de guardias con datos**
GIVEN el usuario tiene permiso `encuentros:ver`
WHEN navega a `/coordinacion/encuentros/guardias`
THEN se muestra una tabla con columnas: Tutor, Materia, Carrera/Cohorte, Día, Horario, Estado, Comentarios
AND filtros disponibles: tutor, materia, estado, rango de fechas
AND un botón "+ Registrar guardia"

**Scenario 2: Registrar guardia exitoso**
GIVEN la vista de guardias
WHEN el usuario hace clic en "+ Registrar guardia"
THEN un formulario modal muestra: tutor (selector de búsqueda), materia, día (datepicker), horario desde/hasta, estado, comentarios
WHEN completa y envía
THEN `POST /api/v1/encuentros/guardias` se llama
AND en 201, la tabla se actualiza
AND un toast "Guardia registrada" se muestra

**Scenario 3: Sin guardias registradas**
GIVEN no hay guardias
WHEN el usuario navega
THEN se muestra "No hay guardias registradas"

**Scenario 4: Filtro por tutor**
GIVEN la tabla con datos
WHEN el usuario selecciona un tutor en el filtro
THEN la query incluye `?tutor_id=...`
AND la tabla se actualiza

**Scenario 5: Exportar guardias**
GIVEN la tabla de guardias con filtros aplicados
WHEN el usuario hace clic en "Exportar CSV"
THEN se descarga un archivo con los datos visibles

**Scenario 6: Loading state**
GIVEN el componente monta
WHILE los datos cargan
THEN tabla esqueleto se muestra

**Scenario 7: Error state**
GIVEN la API falla
THEN se muestra "Error al cargar guardias" con reintento

**Scenario 8: Validación — horario inconsistente**
GIVEN el formulario de registro
WHEN el usuario establece horario_hasta anterior a horario_desde
THEN validación Zod muestra "El horario de fin debe ser posterior al de inicio"
AND el envío se bloquea
