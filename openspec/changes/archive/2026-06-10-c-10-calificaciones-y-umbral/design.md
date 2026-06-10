## Context

El sistema ya tiene el padrón de alumnos (C-09: `EntradaPadron`, `VersionPadron`), la estructura académica (C-06: `Materia`, `Cohorte`), equipos docentes (C-08: `Asignacion`) y audit log (C-05). Este change introduce la capa de calificaciones: modelos, parser de archivos LMS, endpoints REST y configuración de umbrales. Es el eslabón crítico entre la ingesta de datos y el análisis de atrasados (C-11).

Restricciones clave del dominio:
- **Scope aislado por docente** (RN-04): dos docentes en la misma materia ven datos diferentes — cada uno importa y configura su propio umbral. El `(usuario_id × materia_id)` es la clave de scope.
- **Umbral por asignación** (RN-03): el umbral no es de la materia sino de la `Asignacion` del docente en esa materia. Otros docentes no se ven afectados.
- **`aprobado` es derivado, no almacenado como input**: se calcula en el service al momento de importar y al recalcular por cambio de umbral.
- **Multi-tenant row-level** obligatorio en toda tabla nueva.

## Goals / Non-Goals

**Goals:**
- Modelos `Calificacion` y `UmbralMateria` con migraciones.
- Parser LMS que distingue escala numérica (RN-01) y textual (RN-02).
- Flujo preview → confirm para la importación (evita import accidental).
- Endpoint para importar reporte de finalización (RN-07, RN-08).
- CRUD de umbral por asignación con recálculo de `aprobado` al cambiar.
- Vaciar calificaciones scope-isolated (RN-04).
- Audit de `CALIFICACIONES_IMPORTAR`.
- Cobertura de paths críticos con tests (derivación, parser, umbral).

**Non-Goals:**
- Análisis de alumnos atrasados → C-11.
- Ranking, reportes y monitores → C-11.
- Frontend de calificaciones → C-22.
- Comunicaciones → C-12.
- Importación masiva multi-materia (F1.4, coordinación) → puede extenderse después.

## Decisions

### D-01: `aprobado` persiste en la fila, se recalcula en dos momentos

**Decisión**: almacenar `aprobado` como columna en `calificacion`. Se calcula en el service al importar (usando el umbral vigente en ese momento) y se recalcula en batch cuando el docente cambia el umbral.

**Alternativa descartada**: calcular `aprobado` en query al vuelo (JOIN con `umbral_materia`). Fue descartada porque C-11 hace consultas pesadas sobre grandes volúmenes de alumnos; calcular en query incrementaría complejidad y latencia innecesariamente.

**Trade-off**: requiere recálculo batch al cambiar umbral, pero eso es O(N) en filas de la materia del docente — aceptable.

### D-02: parser LMS como utilidad pura en `app/utils/lms_parser.py`

**Decisión**: el parser (detección de columnas, mapeo de valores textuales) vive en un módulo utilitario sin dependencias de ORM ni FastAPI. Recibe los bytes del archivo y devuelve un `ParseResult` (Pydantic) con actividades detectadas y filas de alumnos.

**Alternativa descartada**: parsear directamente en el service. Descartada porque el parser tiene lógica propia testeable independientemente de la DB.

**Beneficio**: los tests del parser son unitarios puros, sin fixtures de DB.

### D-03: flujo preview/confirm con estado en memoria (sin tabla temporal)

**Decisión**: el endpoint `POST /preview` parsea el archivo y devuelve la estructura detectada en la respuesta sin persistir nada. El endpoint `POST /import` recibe el mismo archivo + la selección de actividades y persiste directamente.

**Alternativa descartada**: guardar el resultado del preview en una tabla temporal o en Redis. Descartada por complejidad innecesaria — el archivo es pequeño (CSV/XLSX de una materia) y re-parsear es O(ms).

### D-04: `UmbralMateria` tiene FK a `Asignacion`, no solo a `(usuario_id, materia_id)`

**Decisión**: FK explícita a `Asignacion` para garantizar que el umbral solo existe para docentes realmente asignados a esa materia.

**Beneficio**: la FK actúa como constraint de integridad; no puede existir un umbral para una combinación arbitraria de usuario+materia que no tenga asignación.

### D-05: valores aprobatorios como JSONB array en `UmbralMateria`

**Decisión**: `valores_aprobatorios` se almacena como `JSONB` (lista de strings). El default del sistema es `["Satisfactorio", "Supera lo esperado"]` (RN-02).

**Alternativa descartada**: tabla separada `ValorAprobatorio`. Descartada — es una lista corta y homogénea; JSONB es suficiente y evita un JOIN adicional.

### D-06: recálculo de `aprobado` al cambiar umbral

**Decisión**: cuando el docente hace `PUT /umbral/{materia_id}`, el service recalcula `aprobado` para todas las `Calificacion` del scope `(asignacion_id, materia_id)` en la misma transacción.

**Riesgo aceptado**: si hay miles de filas, la transacción puede ser lenta. Se acepta porque en el escenario real (una comisión universitaria) el volumen es ~20–200 alumnos × ~10–30 actividades = máximo ~6000 filas. Aceptable.

## Risks / Trade-offs

- **[Riesgo] Formato del archivo LMS puede variar entre versiones de Moodle** → Mitigación: el parser detecta columnas por sufijo `(Real)` y valores textuales por lista configurable. Si el formato cambia, solo se actualiza el parser. La lista de valores aprobatorios es configurable por tenant.
- **[Riesgo] Recálculo batch al cambiar umbral puede timeout en comisiones grandes** → Mitigación: en producción, si el volumen crece, mover el recálculo a un background job. Para la escala actual de la plataforma, la transacción síncrona es aceptable.
- **[Trade-off] preview sin estado** → El usuario debe subir el archivo dos veces (preview + confirm). Aceptable para la escala actual; puede optimizarse con upload-and-cache si se necesita.

## Migration Plan

1. Crear migración `008_calificacion_umbral.py` con tablas `calificacion` y `umbral_materia`.
2. No hay datos previos que migrar — las tablas son nuevas.
3. Rollback: `downgrade()` hace `DROP TABLE` en orden inverso (respetando FK).
4. Despliegue sin downtime: las tablas nuevas no afectan código existente.

## Open Questions

- **OQ-01**: ¿El umbral por defecto (60%) es configurable por tenant o es global? La KB dice "configurable por tenant" pero no existe tabla de configuración de tenant aún. Solución provisional: constante `DEFAULT_UMBRAL_PCT = 60` en el service hasta que exista la tabla de configuración.
- **OQ-02**: ¿Se acepta XLSX además de CSV? El LMS de referencia exporta ambos. Solución: soportar ambos desde el primer día usando `openpyxl`/`pandas` o `csv` + `openpyxl` según la extensión del archivo.
