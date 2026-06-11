## ADDED Requirements

### Requirement: Reporte rápido de métricas por asignación
El sistema SHALL exponer `GET /api/analisis/reporte-rapido` que devuelva métricas consolidadas de una asignación: total alumnos, total actividades importadas, cantidad de alumnos con al menos una aprobada, cantidad de atrasados, y porcentaje de aprobación global.

#### Scenario: Reporte con datos importados
- **WHEN** una asignación tiene 20 alumnos con calificaciones cargadas y 14 tienen al menos una actividad aprobada
- **THEN** el reporte devuelve `total_alumnos=20`, `con_aprobadas=14`, `atrasados=6`, `pct_aprobacion=70.0`

#### Scenario: Reporte sin datos importados
- **WHEN** la asignación existe pero no tiene ninguna `Calificacion` registrada
- **THEN** el sistema devuelve el reporte con todos los contadores en cero y un campo `sin_datos=true`

### Requirement: Notas finales agrupadas por asignación
El sistema SHALL calcular una nota final por alumno como promedio de `nota_numerica` de las actividades seleccionadas. El resultado se expone en `GET /api/analisis/notas-finales?asignacion_id=<id>&actividades=<ids>`.

#### Scenario: Nota final calculada sobre actividades seleccionadas
- **WHEN** el PROFESOR consulta notas finales con una selección de 3 actividades numéricas
- **THEN** el sistema devuelve, para cada alumno, el promedio de sus notas en esas 3 actividades con dos decimales de precisión

#### Scenario: Alumno sin nota en alguna actividad seleccionada
- **WHEN** el alumno no tiene `Calificacion` para una actividad de la selección
- **THEN** esa actividad se trata como `0.0` en el cálculo del promedio del alumno

#### Scenario: Sin actividades numéricas seleccionadas
- **WHEN** las actividades seleccionadas no contienen ninguna de escala numérica
- **THEN** el sistema devuelve 422 Unprocessable Entity con mensaje descriptivo

### Requirement: Export de notas finales en CSV
El sistema SHALL permitir descargar las notas finales como archivo CSV mediante `GET /api/analisis/notas-finales/export?asignacion_id=<id>&actividades=<ids>`.

#### Scenario: Descarga de CSV de notas finales
- **WHEN** el PROFESOR solicita el export con una selección válida de actividades
- **THEN** el sistema responde con `Content-Type: text/csv`, `Content-Disposition: attachment; filename="notas_finales_<materia>.csv"` y las filas `alumno,email,nota_final`

### Requirement: Export de trabajos prácticos sin corregir
El sistema SHALL exponer `GET /api/analisis/tps-sin-corregir/export?asignacion_id=<id>` que devuelva en CSV las entregas de escala textual finalizadas (según el reporte de finalización importado) que no tienen calificación registrada (RN-07, RN-08).

#### Scenario: CSV con TPs sin corregir
- **WHEN** el PROFESOR solicita el export de TPs sin corregir para una asignación con datos de finalización cargados
- **THEN** el sistema devuelve un CSV con columnas `alumno, email, actividad, fecha_finalizacion` para cada entrega pendiente de corrección

#### Scenario: Sin entregas pendientes
- **WHEN** todas las actividades textuales finalizadas ya tienen calificación registrada
- **THEN** el sistema devuelve un CSV vacío (solo encabezados) con status 200

#### Scenario: Sin reporte de finalización cargado
- **WHEN** no hay datos de finalización para la asignación
- **THEN** el sistema devuelve 200 con un CSV vacío e incluye un header `X-Sin-Datos-Finalizacion: true`

### Requirement: Guard de permiso atrasados:ver en reportes
El sistema SHALL exigir `atrasados:ver` en todos los endpoints de reportes. El scope (propio vs global) aplica igual que en el módulo de atrasados.

#### Scenario: PROFESOR sin permiso
- **WHEN** un PROFESOR sin `atrasados:ver` accede a `/api/analisis/reporte-rapido`
- **THEN** el sistema devuelve 403 Forbidden
