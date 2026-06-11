## Why

Con C-10 el sistema puede importar calificaciones y computar el campo `aprobado` por alumno y actividad, pero aún no expone ninguna vista analítica sobre esos datos. C-11 cierra esa brecha: incorpora el motor de detección de alumnos atrasados, los monitores de seguimiento y los reportes rápidos que permiten a docentes, tutores y coordinadores actuar sobre los datos ya cargados. Sin este change, C-12 (comunicaciones) no tiene destinatarios que seleccionar, bloqueando el flujo core `importar → analizar → comunicar`.

## What Changes

- **Motor de análisis de atrasados** (F2.2, RN-06): cómputo server-side de qué alumnos están atrasados (actividades faltantes o nota < umbral). Lógica en Services, sin SQL crudo en capa de servicio.
- **Ranking de actividades aprobadas** (F2.3, RN-09): tabla ordenada por cantidad de actividades aprobadas, filtrada a alumnos con al menos una aprobada.
- **Reporte rápido por materia** (F2.4): métricas consolidadas (total alumnos, aprobados, en riesgo, tendencias) a partir de los datos importados.
- **Notas finales agrupadas** (F2.5): cálculo de nota final por alumno sobre actividades seleccionadas; salida exportable.
- **Export de TPs sin corregir** (F2.6, RN-07, RN-08): descarga del listado de entregas de escala textual finalizadas sin nota.
- **Monitor general** (F2.7): vista transversal para COORDINADOR/ADMIN con filtros por materia, regional, comisión, alumno, estado de actividad, criterio de clasificación; con export.
- **Monitor de seguimiento tutor/profesor** (F2.8): vista filtrable por alumnos asignados al usuario; filtros por alumno, correo, comisión, regional, actividad y mínimo cumplido.
- **Monitor de seguimiento coordinación/admin** (F2.9): extiende F2.8 con filtro adicional de rango de fechas.
- Nuevos endpoints bajo `/api/analisis/*` con guard `atrasados:ver`.

## Capabilities

### New Capabilities
- `analisis-atrasados`: Motor de detección de alumnos atrasados (RN-06) y API de consulta filtrable por materia/asignación. Incluye paginación y export CSV.
- `ranking-actividades`: Cómputo y exposición del ranking de actividades aprobadas por alumno (RN-09), filtrado a alumnos con al menos una aprobada.
- `reportes-materia`: Reporte rápido (métricas agregadas), notas finales agrupadas y export de TPs sin corregir (RN-07/08). Un solo spec que cubre F2.4, F2.5 y F2.6.
- `monitores-seguimiento`: Monitores de seguimiento multi-rol (F2.7, F2.8, F2.9) con filtros y export. Vista docente y vista coordinación/admin.

### Modified Capabilities
- `calificaciones-importacion`: Agrega la relación con el flag `finalizado` (reporte de finalización) para el cruce RN-07/RN-08 que usan los reportes de TPs sin corregir. No es un cambio de comportamiento de importación sino una precondición de lectura que este change formaliza.

## Impact

- **Backend**: nuevos módulos `app/services/analisis_service.py`, `app/repositories/analisis_repository.py`, `app/routers/analisis.py`, `app/schemas/analisis.py`. Sin migraciones de schema (los modelos `Calificacion`, `UmbralMateria`, `EntradaPadron` y `VersionPadron` ya existen).
- **Permisos**: permiso `atrasados:ver` debe estar seeded en la matriz de RBAC (C-04). Verificar si ya existe; si no, agregar en migración de datos.
- **Dependencias**: C-09 (padrón + Moodle ingesta) y C-10 (calificaciones + umbral) deben estar completos.
- **Desbloquea**: C-12 `comunicaciones-cola-worker` (requiere lista de alumnos atrasados como origen de destinatarios).
