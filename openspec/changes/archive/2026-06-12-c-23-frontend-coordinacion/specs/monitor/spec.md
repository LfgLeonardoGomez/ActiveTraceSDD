# Monitor — Spec

> Monitor general transversal (COORDINADOR/ADMIN) y auditoría de actividad por docente.

---

## REQ-MO-01: Monitor general transversal

El componente `MonitorGeneralTable` muestra el estado de actividades de todos los alumnos del tenant con filtros avanzados, consumiendo `GET /api/v1/analisis/monitor/general`. Extiende la vista del monitor de PROFESOR/TUTOR con alcance global y filtro por rango de fechas.

### Scenarios

**Scenario 1: Monitor general con datos**
GIVEN el usuario tiene rol COORDINADOR o ADMIN
WHEN navega a `/coordinacion/monitor`
THEN se muestra `MonitorGeneralTable` con columnas: Alumno, Email, Comisión, Regional, Materia, Actividad, Estado, Última actividad
AND los filtros disponibles son: nombre, email, comisión, regional, actividad, materia, rango de fechas (fecha_desde, fecha_hasta), búsqueda libre
AND la tabla está paginada (50 por página)
AND el alcance incluye TODAS las comisiones del tenant (no solo las del usuario)

**Scenario 2: Sin datos de monitoreo**
GIVEN no hay alumnos o actividades en el tenant
WHEN el usuario navega al monitor
THEN se muestra "No se encontraron datos de monitoreo para los filtros seleccionados"
AND los filtros permanecen visibles para ajustar

**Scenario 3: Filtro por rango de fechas**
GIVEN el monitor general está visible
WHEN el usuario establece "Fecha desde: 2025-03-01" y "Fecha hasta: 2025-06-30"
THEN la query incluye `?fecha_desde=2025-03-01&fecha_hasta=2025-06-30`
AND la tabla se actualiza con datos en ese rango

**Scenario 4: Rango de fechas inválido**
GIVEN los filtros de fecha están visibles
WHEN el usuario establece fecha_desde posterior a fecha_hasta
THEN validación muestra "La fecha desde debe ser anterior a la fecha hasta"
AND no se envía la query

**Scenario 5: Múltiples filtros combinados**
GIVEN el monitor general
WHEN el usuario aplica nombre="García" Y comisión="Comisión A" Y materia="Matemática"
THEN todos los parámetros se envían en una sola request
AND la tabla muestra la intersección

**Scenario 6: Limpiar filtros**
GIVEN uno o más filtros activos
WHEN el usuario hace clic en "Limpiar filtros"
THEN todos los filtros se resetearn
AND la tabla se recarga sin parámetros
AND la paginación vuelve a página 1

**Scenario 7: Paginación**
GIVEN la tabla tiene múltiples páginas
WHEN el usuario navega a página 2
THEN `GET /api/v1/analisis/monitor/general?page=2&page_size=50` se llama
AND la tabla muestra la siguiente página
AND "Mostrando 51-100 de {total} registros" se muestra

**Scenario 8: Paginación se resetea al cambiar filtros**
GIVEN el usuario está en página 3
WHEN aplica un nuevo filtro
THEN la página se resetea a 1 implícitamente

**Scenario 9: Exportar monitor**
GIVEN los filtros y datos están visibles
WHEN el usuario hace clic en "Exportar CSV"
THEN se descarga un archivo con los datos actualmente filtrados

**Scenario 10: Loading state**
GIVEN el componente monta o los filtros cambian
WHILE los datos cargan
THEN una tabla esqueleto con 5 filas placeholder se muestra
AND los filtros están deshabilitados

**Scenario 11: Error state**
GIVEN la API falla
THEN se muestra "Error al cargar datos de monitoreo"
AND un botón "Reintentar" está visible
AND los datos previamente cacheados (si existen) permanecen visibles

---

## REQ-MO-02: Auditoría de actividad por docente

El componente `AuditoriaTable` permite consultar el log de actividad de los docentes, consumiendo `GET /api/v1/analisis/monitor/auditoria`.

### Scenarios

**Scenario 1: Auditoría con datos**
GIVEN el usuario tiene permiso `monitor:ver`
WHEN navega a `/coordinacion/monitor/auditoria`
THEN se muestra `AuditoriaTable` con columnas: Fecha/Hora, Docente, Rol, Acción (tipo), Materia, Registros afectados, IP, User-Agent
AND filtros disponibles: rango de fechas, docente, materia, tipo de acción, búsqueda libre
AND la tabla está paginada (50 por página)
AND ordenada por fecha descendente por defecto

**Scenario 2: Sin actividad registrada**
GIVEN no hay acciones registradas en el período
WHEN el usuario navega a auditoría
THEN se muestra "No hay actividad registrada para los filtros seleccionados"

**Scenario 3: Filtro por tipo de acción**
GIVEN la tabla de auditoría está visible
WHEN el usuario selecciona "importación" en el filtro de tipo de acción
THEN la query incluye `?tipo_accion=importacion`
AND la tabla se actualiza mostrando solo acciones de importación

**Scenario 4: Filtro por docente**
GIVEN la tabla de auditoría
WHEN el usuario selecciona un docente en el filtro
THEN la query incluye `?docente_id=...`
AND la tabla se actualiza

**Scenario 5: Filtro por rango de fechas**
GIVEN la tabla de auditoría
WHEN el usuario establece un rango de fechas
THEN las acciones fuera del rango se excluyen

**Scenario 6: Búsqueda libre**
GIVEN la tabla de auditoría
WHEN el usuario escribe en el campo de búsqueda libre
THEN la query incluye `?q=...`
AND los resultados se filtran por coincidencia en cualquier campo textual

**Scenario 7: Exportar auditoría**
GIVEN los filtros están aplicados
WHEN el usuario hace clic en "Exportar CSV"
THEN se descarga un archivo con los datos de auditoría filtrados

**Scenario 8: Paginación**
GIVEN la auditoría tiene múltiples páginas
WHEN el usuario navega entre páginas
THEN la paginación funciona consistentemente con page_size=50

**Scenario 9: Detalle de acción (expandir fila)**
GIVEN la tabla de auditoría
WHEN el usuario hace clic en una fila
THEN la fila se expande mostrando detalles adicionales de la acción (request payload parcial, response status, duración)
AND se muestra el User-Agent completo

**Scenario 10: Loading state**
GIVEN el componente monta
WHILE los datos cargan
THEN tabla esqueleto con 5 filas placeholder se muestra
AND los filtros están deshabilitados

**Scenario 11: Error state**
GIVEN la API falla
THEN se muestra "Error al cargar auditoría" con botón "Reintentar"
