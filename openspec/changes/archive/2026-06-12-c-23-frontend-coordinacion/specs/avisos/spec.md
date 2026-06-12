# Avisos — Spec

> Publicación de avisos del sistema con alcance (global/materia/cohorte), severidad, vigencia y requerimiento de acknowledgment.

---

## REQ-AV-01: CRUD de avisos

El componente `AvisoForm` + `AvisoCard` permite crear, editar, publicar y eliminar avisos, consumiendo `GET /api/v1/avisos`, `POST /api/v1/avisos`, `PUT /api/v1/avisos/{id}` y `DELETE /api/v1/avisos/{id}`.

### Scenarios

**Scenario 1: Listado de avisos publicados**
GIVEN el usuario tiene permiso `avisos:ver`
WHEN navega a `/coordinacion/avisos`
THEN se muestra una lista de `AvisoCard` con: título, severidad (badge color), alcance, vigencia (fecha_desde — fecha_hasta), requiere_ack (sí/no), estado (borrador/publicado/vencido)
AND las cards se ordenan por fecha de creación descendente
AND filtros disponibles: estado, severidad, alcance

**Scenario 2: Sin avisos**
GIVEN no hay avisos creados
WHEN el usuario navega
THEN se muestra "No hay avisos publicados"
AND un botón "+ Nuevo aviso" está visible

**Scenario 3: Crear aviso exitoso**
GIVEN el usuario tiene permiso `avisos:crear`
WHEN navega a `/coordinacion/avisos/nuevo`
THEN `AvisoForm` muestra campos: título, cuerpo (textarea con soporte de markdown), alcance, roles destinatarios, severidad (informativo/advertencia/crítico), fecha_desde, fecha_hasta, requiere_ack (checkbox)
WHEN completa y hace clic en "Publicar"
THEN `POST /api/v1/avisos` se llama con todos los datos
AND en 201, se redirige a `/coordinacion/avisos`
AND un toast "Aviso publicado correctamente" se muestra

**Scenario 4: Guardar como borrador**
GIVEN el formulario de creación
WHEN el usuario hace clic en "Guardar borrador" en lugar de "Publicar"
THEN `POST /api/v1/avisos` se llama con `{ estado: "borrador" }`
AND el aviso aparece en el listado con estado "borrador"
AND no es visible para los destinatarios hasta que se publique

**Scenario 5: Editar aviso**
GIVEN el listado de avisos
WHEN el usuario hace clic en editar de un aviso en estado "borrador" o "publicado"
THEN `AvisoForm` se abre precargado con todos los campos
WHEN modifica el cuerpo y hace clic en "Guardar"
THEN `PUT /api/v1/avisos/{id}` se llama
AND el listado refleja los cambios

**Scenario 6: Eliminar aviso con confirmación**
GIVEN el listado de avisos
WHEN el usuario hace clic en eliminar
THEN un diálogo de confirmación muestra "¿Eliminar el aviso {título}?"
WHEN confirma
THEN `DELETE /api/v1/avisos/{id}` se llama (soft delete)
AND la card desaparece del listado

**Scenario 7: Validación — fecha de vigencia incorrecta**
GIVEN el formulario de aviso
WHEN el usuario establece fecha_hasta anterior a fecha_desde
THEN validación Zod muestra "La fecha de fin debe ser posterior a la fecha de inicio"
AND el envío se bloquea

**Scenario 8: Validación — cuerpo vacío**
GIVEN el formulario
WHEN el usuario intenta publicar con el cuerpo vacío
THEN validación Zod muestra "El cuerpo del aviso no puede estar vacío"

**Scenario 9: Loading state**
GIVEN el componente monta
WHILE los datos cargan
THEN 3 skeleton cards con shimmer se muestran

**Scenario 10: Error state**
GIVEN la API falla
THEN se muestra "Error al cargar avisos" con botón "Reintentar"

---

## REQ-AV-02: Selección de alcance y roles destinatarios

El componente `AvisoScopeSelector` permite configurar el alcance del aviso (global/materia/cohorte) y los roles destinatarios.

### Scenarios

**Scenario 1: Alcance global — visible para todos los usuarios del tenant**
GIVEN el formulario de aviso
WHEN el usuario selecciona alcance = "global"
THEN los selectores de materia y cohorte se ocultan (no aplican)
AND el aviso será visible para todos los usuarios activos del tenant

**Scenario 2: Alcance por materia**
GIVEN el formulario de aviso
WHEN el usuario selecciona alcance = "materia"
THEN aparece un selector de materia (dropdown)
WHEN selecciona una materia
THEN el aviso será visible solo para usuarios relacionados con esa materia
AND el selector de cohorte permanece opcional para filtrar aún más

**Scenario 3: Alcance por cohorte**
GIVEN el formulario de aviso
WHEN el usuario selecciona alcance = "cohorte"
THEN aparece un selector de cohorte
WHEN selecciona "MAR-2025"
THEN el aviso será visible solo para usuarios de esa cohorte

**Scenario 4: Selección de roles destinatarios**
GIVEN el formulario de aviso
WHEN el usuario ve la sección "Visible para roles"
THEN se muestran checkboxes para: TUTOR, PROFESOR, COORDINADOR, ADMIN, FINANZAS, NEXO
WHEN selecciona "PROFESOR" y "TUTOR"
THEN solo esos roles verán el aviso
AND si no selecciona ninguno, por defecto se seleccionan todos

---

## REQ-AV-03: Vigencia de avisos

El aviso tiene una ventana de visibilidad definida por fecha_desde y fecha_hasta.

### Scenarios

**Scenario 1: Aviso activo dentro de vigencia**
GIVEN un aviso con fecha_desde = 2025-03-01 y fecha_hasta = 2025-06-30
WHEN un usuario accede al sistema el 2025-04-15
THEN el aviso es visible y se muestra en su bandeja/panel

**Scenario 2: Aviso aún no activo (fecha futura)**
GIVEN un aviso con fecha_desde = 2025-07-01
WHEN un usuario accede el 2025-06-15
THEN el aviso NO es visible para ningún destinatario
AND en el listado de gestión aparece con estado "programado"

**Scenario 3: Aviso vencido**
GIVEN un aviso con fecha_hasta = 2025-03-01
WHEN un usuario accede el 2025-06-15
THEN el aviso NO es visible para ningún destinatario
AND en el listado de gestión aparece con estado "vencido"
AND el ADMIN/COORDINADOR puede extender la vigencia editando el aviso

**Scenario 4: Publicación inmediata (sin fecha_desde)**
GIVEN el formulario de aviso
WHEN el usuario deja el campo fecha_desde vacío
THEN el aviso se publica inmediatamente al crearlo
AND fecha_desde se setea a la fecha/hora actual automáticamente

**Scenario 5: Vigencia indefinida (sin fecha_hasta)**
GIVEN el formulario
WHEN el usuario deja el campo fecha_hasta vacío
THEN el aviso no tiene fecha de expiración
AND se muestra un indicador "Sin vencimiento" en la card

---

## REQ-AV-04: Requerimiento de acknowledgment (ack)

Los avisos pueden requerir confirmación de lectura por parte de los destinatarios.

### Scenarios

**Scenario 1: Aviso con requiere_ack = true**
GIVEN un aviso publicado con `requiere_ack = true`
WHEN un destinatario abre el aviso
THEN además del contenido, se muestra un botón "Confirmar lectura"
WHEN hace clic en "Confirmar lectura"
THEN `POST /api/v1/avisos/{id}/ack` se llama
AND el botón cambia a "Leído" (deshabilitado)
AND un timestamp de lectura se registra

**Scenario 2: Aviso sin requiere_ack**
GIVEN un aviso con `requiere_ack = false`
WHEN un destinatario abre el aviso
THEN el contenido se muestra sin botón de confirmación
AND no se requiere ninguna acción del destinatario

**Scenario 3: Vista de acknowledgments en gestión**
GIVEN el listado de avisos en la vista de gestión
WHEN el usuario abre el detalle de un aviso con `requiere_ack = true`
THEN se muestra una tabla: Destinatario, Rol, Leído (sí/no), Fecha de lectura
AND un contador "{N}/{M} destinatarios leyeron este aviso"

**Scenario 4: Aviso crítico con ack obligatorio**
GIVEN un aviso con severidad = "crítico" y `requiere_ack = true`
WHEN un destinatario no ha leído el aviso
THEN el aviso se destaca visualmente (badge rojo, posición prioritaria)
AND permanece destacado hasta que el destinatario confirme lectura
