## Context

C-10 introdujo los modelos `Calificacion` y `UmbralMateria` con el campo derivado `aprobado`. C-09 aportó `VersionPadron` y `EntradaPadron`. Toda la información necesaria para el análisis ya existe en la base de datos; este change sólo expone una capa analítica sobre esos datos. No hay cambios de schema.

El sistema actualmente no tiene ningún endpoint bajo `/api/analisis/`. El permiso `atrasados:ver` debe verificarse en la seed de RBAC (C-04): si ya no está presente, se agrega en un script de datos.

## Goals / Non-Goals

**Goals:**
- Detectar alumnos atrasados por asignación docente (actividades faltantes o nota < umbral).
- Exponer ranking de actividades aprobadas, reportes rápidos, notas finales y export de TPs sin corregir.
- Proveer monitores multi-rol con filtros y export CSV.
- Mantener todo el cómputo en la capa Service; las queries de agregación van al Repository.

**Non-Goals:**
- No se almacenan resultados de análisis (sin tablas de cache ni materialización).
- No se implementa notificación automática de atrasados (eso es C-12).
- No se modifican los modelos de importación (C-09/C-10 ya completos).

## Decisions

### D-01 — Sin persistencia de resultados analíticos
**Decisión**: el análisis se calcula on-demand en cada request; no se cachea en DB.  
**Alternativa descartada**: tabla `AnalisisSnapshot` con TTL. Se descartó porque los datos cambian con cada importación y la complejidad de invalidación supera el beneficio para el volumen esperado (~200 alumnos por materia).  
**Trade-off**: queries ligeramente más lentas en monitores globales, aceptable para el volumen actual.

### D-02 — Queries de agregación en Repository, no en Service
**Decisión**: las queries con JOINs y agregaciones (COUNT, GROUP BY) viven en `AnalisisRepository`. El Service sólo orquesta y aplica lógica de negocio pura (como el cruce con umbral).  
**Rationale**: respeta la regla dura #11 (sin lógica de negocio en Routers; sin acceso directo a DB en Services).

### D-03 — Export como streaming response
**Decisión**: el export CSV se emite como `StreamingResponse` con `text/csv`. No se persiste el archivo en disco.  
**Rationale**: sin dependencias nuevas (usa `csv` de stdlib Python), sin consumo de disco, compatible con los patrones existentes.

### D-04 — Permiso único `atrasados:ver`
**Decisión**: un solo permiso `atrasados:ver` protege todos los endpoints de análisis. Los filtros de scope (propio vs global) se resuelven en Service con `is_propio` del `PermissionContext` (patrón ya establecido en C-04).  
**Alternativa descartada**: permisos separados por sub-feature. Se descartó por complejidad innecesaria; el scope ya diferencia qué datos devuelve.

### D-05 — Scope de "atrasado" es por asignación docente
**Decisión**: un alumno se evalúa como atrasado en el contexto de una asignación específica (docente × materia), no globalmente. Esto respeta el scope aislado de RN-04 y la configuración de umbral por asignación (E8).

## Risks / Trade-offs

- **[Riesgo] Monitor global lento con muchos alumnos** → Mitigación: paginación obligatoria (máx 100 por página), índice en `(tenant_id, materia_id, entrada_padron_id)` en `Calificacion` (ya creado en C-10).
- **[Riesgo] `atrasados:ver` no presente en seed de C-04** → Mitigación: tarea explícita en tasks.md para verificar y agregar si falta. Fail-closed: sin permiso → 403.
- **[Trade-off] On-demand vs cache** → Decisión D-01 prioriza simplicidad. Si el monitor global se vuelve inaceptablemente lento, se puede materializar en un step futuro sin cambiar la API.

## Migration Plan

Sin migraciones de schema. El único paso de deploy es verificar que `atrasados:ver` esté presente en la tabla `Permiso` y en la matriz `RolPermiso` del seed.

## Open Questions

- ¿El export del monitor general debe incluir también alumnos `aprobado = True` (export total) o sólo los atrasados? (La KB dice "exportar" en F2.7 sin especificar filtro.) Decisión provisional: export respeta los filtros activos en la vista; si no hay filtro de estado, exporta todo.
