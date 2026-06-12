# Equipos Docentes — Spec

> Gestión de equipos docentes: ABM de usuarios docentes (ADMIN), vista mis equipos, asignaciones individuales y masivas, clonar entre períodos, vigencia general y exportación.

---

## REQ-EQ-01: Vista "Mis Equipos" muestra las comisiones y materias asignadas al usuario

La página `MisEquipos` consume `GET /api/v1/equipos/mis-equipos` y presenta un resumen de todas las comisiones y materias en las que el usuario está asignado, con su rol, carrera, cohorte, comisiones asociadas, vigencia y estado.

### Scenarios

**Scenario 1: Usuario con asignaciones activas**
GIVEN el usuario autenticado tiene una o más asignaciones activas
WHEN navega a `/coordinacion/equipos`
THEN se muestran tarjetas (`EquipoCard`) agrupadas por materia×cohorte
AND cada tarjeta muestra: materia, carrera, cohorte, rol(es), vigencia (fecha_desde — fecha_hasta), estado
AND los filtros de estado, materia, rol, carrera y cohorte están visibles en la parte superior
AND un contador "Mostrando {N} asignaciones" se muestra encima de la lista

**Scenario 2: Sin asignaciones**
GIVEN el usuario no tiene asignaciones activas
WHEN navega a `/coordinacion/equipos`
THEN se muestra el estado vacío "No tenés equipos asignados"
AND los filtros se muestran deshabilitados
AND un botón "Ir a estructura" (si el rol es COORDINADOR/ADMIN) permite navegar a `/coordinacion/estructura`

**Scenario 3: Filtro por estado**
GIVEN la lista de equipos está visible
WHEN el usuario selecciona "Inactivo" en el filtro de estado
THEN la query se re-ejecuta con `?estado=inactivo`
AND la tabla se actualiza mostrando solo asignaciones inactivas

**Scenario 4: Filtro por materia**
GIVEN la lista de equipos está visible
WHEN el usuario selecciona una materia del filtro
THEN la query se re-ejecuta con `?materia_id=...`
AND la tabla se actualiza

**Scenario 5: Múltiples filtros combinados**
GIVEN los filtros de estado, materia y rol están disponibles
WHEN el usuario selecciona estado="activo" Y materia="Matemática" Y rol="PROFESOR"
THEN la query incluye los tres parámetros
AND la tabla muestra la intersección de todos los filtros

**Scenario 6: Limpiar filtros**
GIVEN uno o más filtros están activos
WHEN el usuario hace clic en "Limpiar filtros"
THEN todos los filtros vuelven a sus valores por defecto
AND la query se re-ejecuta sin parámetros de filtro

**Scenario 7: Loading state**
GIVEN el componente monta
WHILE los datos se están cargando
THEN se muestran 3 esqueletos de `EquipoCard` con shimmer animation
AND los filtros aparecen deshabilitados

**Scenario 8: Error state**
GIVEN el componente monta
WHEN `GET /api/v1/equipos/mis-equipos` falla con error de red o 500
THEN se muestra "Error al cargar tus equipos"
AND un botón "Reintentar" aparece
AND los filtros se mantienen visibles

---

## REQ-EQ-02: ADMIN puede ABM usuarios del equipo docente

El componente `UsuarioForm` + `UsuarioTable` permite al ADMIN crear, editar y activar/desactivar usuarios con rol docente, consumiendo `GET /api/v1/equipos/usuarios`, `POST /api/v1/equipos/usuarios` y `PUT /api/v1/equipos/usuarios/{id}`.

### Scenarios

**Scenario 1: Vista de listado de usuarios (ADMIN)**
GIVEN el usuario tiene rol ADMIN
WHEN navega a `/coordinacion/equipos/usuarios`
THEN se muestra una tabla (`UsuarioTable`) con columnas: Nombre, Email, Rol, Regional, Estado (activo/inactivo), Última actualización
AND un botón "+ Nuevo usuario" está visible arriba a la derecha
AND la tabla está paginada (50 por página)

**Scenario 2: Crear usuario — flujo exitoso**
GIVEN el ADMIN está en el listado de usuarios
WHEN hace clic en "+ Nuevo usuario"
THEN se abre `UsuarioForm` en modo creación con campos: nombre, email, rol (PROFESOR/TUTOR/NEXO/COORDINADOR), regional, estado
WHEN completa todos los campos requeridos y envía
THEN `POST /api/v1/equipos/usuarios` se llama con los datos del formulario
AND en 201, la tabla se actualiza con el nuevo usuario
AND un toast "Usuario creado correctamente" se muestra
AND el formulario se cierra

**Scenario 3: Crear usuario — validación de email duplicado**
GIVEN el formulario de creación está abierto
WHEN el usuario ingresa un email ya registrado y envía
THEN `POST /api/v1/equipos/usuarios` retorna 409
AND se muestra el error "El email ya está registrado" inline en el campo email
AND el formulario permanece abierto para corrección

**Scenario 4: Crear usuario — validación de formulario falla (Zod)**
GIVEN el formulario de creación está abierto
WHEN el usuario intenta enviar sin completar campos requeridos (ej: nombre vacío, email inválido)
THEN la validación de Zod impide el envío
AND los mensajes de error aparecen debajo de cada campo inválido
AND ningún request se envía al backend

**Scenario 5: Editar usuario**
GIVEN la tabla de usuarios está visible
WHEN el ADMIN hace clic en el ícono de editar de una fila
THEN `UsuarioForm` se abre en modo edición precargado con los datos del usuario
WHEN modifica el rol y guarda
THEN `PUT /api/v1/equipos/usuarios/{id}` se llama con los datos actualizados
AND la tabla refleja el cambio
AND un toast "Usuario actualizado correctamente" se muestra

**Scenario 6: Desactivar usuario con confirmación**
GIVEN la tabla de usuarios está visible
WHEN el ADMIN hace clic en el toggle de estado de un usuario activo
THEN un diálogo de confirmación aparece: "¿Desactivar usuario {nombre}? El usuario no podrá acceder al sistema hasta que sea reactivado."
WHEN el ADMIN confirma
THEN `PUT /api/v1/equipos/usuarios/{id}` se llama con `{ activo: false }`
AND el estado del usuario cambia a inactivo en la tabla

**Scenario 7: Loading state**
GIVEN el ADMIN navega a usuarios
WHILE los datos se cargan
THEN una tabla esqueleto con 5 filas placeholder se muestra
AND los botones de acción están deshabilitados

**Scenario 8: Error state**
GIVEN el listado de usuarios
WHEN `GET /api/v1/equipos/usuarios` falla
THEN se muestra "Error al cargar usuarios" con botón "Reintentar"
AND los datos cacheados (si existen) permanecen visibles

**Scenario 9: Permiso denegado (no ADMIN)**
GIVEN el usuario autenticado NO tiene rol ADMIN
WHEN intenta navegar a `/coordinacion/equipos/usuarios`
THEN el componente `PermissionGuard` muestra 403
AND la entrada de sidebar "Usuarios" no se renderiza para este usuario

---

## REQ-EQ-03: Gestión de asignaciones individuales

El componente `AsignacionForm` permite a COORDINADOR/ADMIN consultar y crear asignaciones individuales de docentes a materia×carrera×cohorte×rol, consumiendo `GET /api/v1/equipos/asignaciones` y `POST /api/v1/equipos/asignaciones`.

### Scenarios

**Scenario 1: Vista de asignaciones con filtros**
GIVEN el usuario es COORDINADOR o ADMIN
WHEN navega a `/coordinacion/equipos/asignaciones`
THEN se muestra la tabla `AsignacionTable` con columnas: Docente, Materia, Carrera, Cohorte, Rol, Vigencia (desde/hasta), Estado
AND los filtros disponibles son: materia, carrera, cohorte, docente (búsqueda por nombre), rol
AND la tabla está paginada

**Scenario 2: Sin asignaciones**
GIVEN no existen asignaciones en el tenant
WHEN el usuario accede a la vista
THEN se muestra "No hay asignaciones registradas"
AND un botón "Crear primera asignación" está visible

**Scenario 3: Crear asignación individual exitosa**
GIVEN la vista de asignaciones está visible
WHEN el usuario hace clic en "+ Nueva asignación"
THEN `AsignacionForm` muestra campos: docente (selector de búsqueda), materia (dropdown), carrera, cohorte, rol, fecha_desde, fecha_hasta
WHEN completa y envía
THEN `POST /api/v1/equipos/asignaciones` se llama con `{ docente_id, materia_id, carrera_id, cohorte_id, rol, fecha_desde, fecha_hasta }`
AND en 201, la tabla se actualiza
AND un toast "Asignación creada correctamente" se muestra

**Scenario 4: Crear asignación — docente ya asignado al mismo materia×rol**
GIVEN el formulario de asignación está abierto
WHEN el usuario selecciona un docente que ya tiene una asignación activa para la misma materia y rol
THEN `POST /api/v1/equipos/asignaciones` retorna 409
AND se muestra "El docente ya está asignado a esta materia con ese rol"
AND el formulario permanece abierto

**Scenario 5: Crear asignación — fecha inválida (hasta antes que desde)**
GIVEN el formulario
WHEN el usuario setea fecha_hasta anterior a fecha_desde
THEN la validación de Zod muestra "La fecha de fin debe ser posterior a la fecha de inicio"
AND el botón de envío permanece deshabilitado

**Scenario 6: Buscar docente por nombre**
GIVEN el selector de docente en el formulario
WHEN el usuario escribe al menos 3 caracteres
THEN se muestra un dropdown con resultados de búsqueda
WHEN selecciona un docente
THEN el `docente_id` se asigna al formulario

**Scenario 7: Loading state**
GIVEN el usuario navega a asignaciones
WHILE los datos cargan
THEN una tabla esqueleto se muestra
AND los filtros aparecen deshabilitados

**Scenario 8: Error state**
GIVEN la vista de asignaciones
WHEN `GET /api/v1/equipos/asignaciones` falla
THEN se muestra "Error al cargar asignaciones" con botón "Reintentar"

---

## REQ-EQ-04: Asignación masiva de docentes

El componente `AsignacionMasivaForm` permite seleccionar múltiples docentes y asignarlos en bloque a una combinación materia×carrera×cohorte×rol, consumiendo `POST /api/v1/equipos/asignaciones/masiva`.

### Scenarios

**Scenario 1: Asignación masiva exitosa**
GIVEN el usuario es COORDINADOR o ADMIN
WHEN navega a `/coordinacion/equipos/asignaciones/masiva`
THEN el formulario muestra: selector multi-select de docentes (con búsqueda), materia, carrera, cohorte, rol, fecha_desde, fecha_hasta
WHEN selecciona 5 docentes, completa los demás campos y envía
THEN `POST /api/v1/equipos/asignaciones/masiva` se llama con los datos
AND en 200, se muestra un resumen "Se crearon {N} asignaciones correctamente"
AND un botón "Volver a asignaciones" permite navegar al listado
AND las queries de asignaciones se invalidan

**Scenario 2: Sin docentes seleccionados**
GIVEN el formulario masivo está visible
WHEN el usuario intenta enviar sin seleccionar ningún docente
THEN la validación de Zod muestra "Seleccioná al menos un docente"
AND el botón de envío permanece deshabilitado

**Scenario 3: Selección múltiple con búsqueda**
GIVEN el multi-select de docentes
WHEN el usuario escribe "García" en la búsqueda
THEN el dropdown filtra a solo los docentes que contienen "García" en el nombre
WHEN el usuario selecciona 3 resultados
THEN los chips con los nombres aparecen en el campo de selección
AND se puede remover cada chip individualmente

**Scenario 4: Asignación masiva con errores parciales**
GIVEN el envío masivo se procesó
WHEN el backend retorna 200 con `{ created: 8, errors: [{ docente_id: "x", motivo: "Ya asignado" }] }`
THEN se muestra un resumen "Se crearon 8 asignaciones. 1 error."
AND los errores se listan en una sección expandible debajo del resumen

**Scenario 5: Error de red**
GIVEN el formulario masivo está completo
WHEN el envío falla por error de red
THEN se muestra "Error de conexión. Verificá e intentá de nuevo."
AND el formulario conserva los valores para reintento

**Scenario 6: Loading state durante el envío**
GIVEN el usuario hizo clic en "Asignar"
WHILE el POST se procesa
THEN el botón muestra spinner y "Asignando..."
AND todos los campos se deshabilitan

---

## REQ-EQ-05: Clonar equipo docente entre períodos

El componente `ClonarEquipoForm` permite duplicar asignaciones de un equipo origen a un destino, consumiendo `POST /api/v1/equipos/clonar`.

### Scenarios

**Scenario 1: Clonación exitosa**
GIVEN el usuario es COORDINADOR o ADMIN
WHEN navega a `/coordinacion/equipos/clonar`
THEN el formulario muestra dos selectores: "Equipo origen" (materia×carrera×cohorte) y "Equipo destino" (materia×carrera×cohorte)
WHEN selecciona origen = "Matemática / MAR-2025" y destino = "Matemática / AGO-2025"
AND hace clic en "Clonar equipo"
THEN `POST /api/v1/equipos/clonar` se llama con `{ origen: { materia_id, cohorte_id }, destino: { materia_id, cohorte_id } }`
AND en 200, se muestra "Equipo clonado correctamente — {N} asignaciones creadas"
AND las queries de asignaciones se invalidan

**Scenario 2: Origen sin asignaciones**
GIVEN el formulario de clonación
WHEN el usuario selecciona un origen que no tiene asignaciones
THEN se muestra "El equipo origen no tiene asignaciones para clonar"
AND el botón "Clonar equipo" está deshabilitado

**Scenario 3: Destino ya tiene asignaciones (confirmación)**
GIVEN el formulario con origen y destino seleccionados
WHEN el destino ya tiene asignaciones existentes
THEN un mensaje de advertencia aparece: "El destino ya tiene {N} asignaciones. La clonación agregará las del origen. ¿Querés continuar?"
AND el botón "Clonar" cambia a "Clonar de todas formas"
AND se requiere confirmación explícita

**Scenario 4: Mismo origen y destino**
GIVEN ambos selectores tienen valores
WHEN el usuario selecciona el mismo equipo en origen y destino
THEN la validación muestra "El origen y el destino deben ser diferentes"
AND el botón de envío se deshabilita

**Scenario 5: Loading state**
GIVEN el usuario hizo clic en "Clonar equipo"
WHILE el POST se procesa
THEN el botón muestra spinner con "Clonando equipo..."
AND los selectores están deshabilitados

**Scenario 6: Error state**
GIVEN el envío de clonación
WHEN el backend retorna error (500, 422)
THEN se muestra "Error al clonar el equipo" con el mensaje del backend
AND el formulario permanece editable para reintento

---

## REQ-EQ-06: Modificar vigencia general del equipo

El componente `VigenciaEditor` permite actualizar las fechas de vigencia de todas las asignaciones de un equipo en una sola operación, consumiendo `PUT /api/v1/equipos/vigencia`.

### Scenarios

**Scenario 1: Actualizar vigencia exitosa**
GIVEN el usuario es COORDINADOR o ADMIN
WHEN navega a `/coordinacion/equipos/vigencia`
THEN el formulario muestra: selector de equipo (materia×cohorte) y dos datepickers: "Vigencia desde" y "Vigencia hasta"
WHEN selecciona un equipo y establece fecha_desde = 2025-08-01 y fecha_hasta = 2026-02-28
AND hace clic en "Actualizar vigencia"
THEN `PUT /api/v1/equipos/vigencia` se llama con `{ equipo_id, fecha_desde: "2025-08-01", fecha_hasta: "2026-02-28" }`
AND en 200, se muestra "Vigencia actualizada para {N} asignaciones"
AND las queries de equipos se invalidan

**Scenario 2: Sin equipo seleccionado**
GIVEN el formulario de vigencia
WHEN el usuario no ha seleccionado ningún equipo
THEN el botón "Actualizar vigencia" está deshabilitado
AND los datepickers están deshabilitados

**Scenario 3: Rango de fechas inválido**
GIVEN un equipo está seleccionado
WHEN el usuario establece vigencia_hasta anterior a vigencia_desde
THEN la validación de Zod muestra "La fecha de fin debe ser posterior a la fecha de inicio"
AND el envío se bloquea

**Scenario 4: Confirmación antes de actualizar**
GIVEN el formulario completo con fechas válidas
WHEN el usuario hace clic en "Actualizar vigencia"
THEN un diálogo de confirmación muestra "¿Actualizar la vigencia de todas las asignaciones de {equipo}? Se modificarán {N} asignaciones."
AND botones "Cancelar" y "Confirmar"
WHEN el usuario confirma
THEN el PUT se ejecuta

**Scenario 5: Loading state**
GIVEN la confirmación se realizó
WHILE el PUT se procesa
THEN el botón muestra spinner con "Actualizando vigencia..."

**Scenario 6: Error state**
GIVEN el PUT falla
THEN se muestra "Error al actualizar la vigencia" con botón "Reintentar"

---

## REQ-EQ-07: Exportar equipo docente

El botón `ExportButton` permite descargar un CSV con el detalle de todas las asignaciones de un equipo, consumiendo `GET /api/v1/equipos/export`.

### Scenarios

**Scenario 1: Exportar equipo exitoso**
GIVEN el usuario es COORDINADOR o ADMIN
WHEN navega a `/coordinacion/equipos/exportar`
THEN se muestra un selector de equipo (materia×cohorte) y un botón "Exportar CSV"
WHEN selecciona un equipo y hace clic en "Exportar CSV"
THEN `GET /api/v1/equipos/export?equipo_id=X` se ejecuta como descarga directa (Blob)
AND el navegador descarga un archivo `equipo_{materia}_{cohorte}.csv`
AND un toast "Exportación completada" se muestra

**Scenario 2: Sin equipo seleccionado**
GIVEN la página de exportación
WHEN no hay equipo seleccionado
THEN el botón "Exportar CSV" está deshabilitado
AND se muestra "Seleccioná un equipo para exportar"

**Scenario 3: Error en la exportación**
GIVEN un equipo está seleccionado
WHEN el usuario hace clic en "Exportar CSV"
AND `GET /api/v1/equipos/export` retorna 500
THEN se muestra "Error al exportar el equipo. Intentá de nuevo."
AND el selector permanece con la selección actual

**Scenario 4: Loading state durante exportación**
GIVEN el usuario inició la exportación
WHILE la descarga se procesa
THEN el botón muestra spinner con "Exportando..."
AND el selector está deshabilitado
