## 1. Modelos y Migración

- [x] 1.1 Crear `app/models/calificacion.py` con modelo SQLAlchemy `Calificacion` (tenant_id, entrada_padron_id, materia_id, actividad, nota_numerica, nota_textual, aprobado, origen enum, importado_at, soft delete)
- [x] 1.2 Crear `app/models/umbral_materia.py` con modelo SQLAlchemy `UmbralMateria` (tenant_id, asignacion_id, materia_id, umbral_pct, valores_aprobatorios JSONB)
- [x] 1.3 Crear migración Alembic `alembic/versions/008_calificacion_umbral.py` — tablas `calificacion` y `umbral_materia` con FK, índices por `(tenant_id, materia_id)` y `(entrada_padron_id, actividad)` unique constraint
- [x] 1.4 Registrar modelos en `app/models/__init__.py`

## 2. Schemas Pydantic

- [x] 2.1 Crear `app/schemas/calificacion.py` — `CalificacionBase`, `CalificacionCreate`, `CalificacionRead`, `ImportPreviewRequest`, `ImportPreviewResponse` (lista de actividades detectadas + alumnos), `ImportConfirmRequest` (actividades seleccionadas), `ImportConfirmResponse` (conteo de filas importadas)
- [x] 2.2 Crear `app/schemas/umbral.py` — `UmbralMateriaRead`, `UmbralMateriaUpsert` (umbral_pct, valores_aprobatorios), todos con `model_config = ConfigDict(extra='forbid')`

## 3. Parser LMS

- [x] 3.1 Crear `app/utils/lms_parser.py` — `LMSParser` con método `parse_calificaciones(file_bytes, filename) -> ParseResult`. Detecta columnas numéricas (`*(Real)`) y textuales. Devuelve `ParseResult` (Pydantic) con `actividades: list[ActividadDetectada]` y `alumnos: list[AlumnoFila]`
- [x] 3.2 Agregar soporte para CSV y XLSX (detectar por extensión; XLSX usa `openpyxl`)
- [x] 3.3 Crear `app/utils/finalizacion_parser.py` — `parse_finalizacion(file_bytes, filename) -> FinalizacionResult` — detecta actividades completadas por alumno desde el reporte de finalización del LMS

## 4. Repositories

- [x] 4.1 Crear `app/repositories/calificacion_repository.py` — `CalificacionRepository` con métodos: `bulk_upsert(calificaciones)`, `get_by_scope(tenant_id, usuario_id, materia_id)`, `recalculate_aprobado(asignacion_id, materia_id, umbral_pct, valores_aprobatorios)`, `soft_delete_scope(tenant_id, usuario_id, materia_id)` — todos con filtro `tenant_id`
- [x] 4.2 Crear `app/repositories/umbral_repository.py` — `UmbralRepository` con métodos: `get_by_asignacion(tenant_id, asignacion_id, materia_id)`, `upsert(umbral_data)` — con filtro `tenant_id`

## 5. Services

- [x] 5.1 Crear `app/services/calificacion_service.py` — `CalificacionService` con:
  - `preview_import(file, materia_id, usuario) -> ImportPreviewResponse` — parsea y devuelve actividades sin persistir
  - `confirm_import(file, materia_id, actividades_seleccionadas, usuario) -> ImportConfirmResponse` — persiste calificaciones, calcula `aprobado`, registra audit `CALIFICACIONES_IMPORTAR`
  - `vaciar_materia(materia_id, usuario)` — soft delete scope-isolated (RN-04)
- [x] 5.2 Crear `app/services/finalizacion_service.py` — `FinalizacionService` con `detectar_sin_corregir(file, materia_id, usuario) -> list[EntregaSinCorregir]` — cruza reporte con calificaciones existentes (RN-07, RN-08)
- [x] 5.3 Crear `app/services/umbral_service.py` — `UmbralService` con:
  - `get_umbral(materia_id, usuario) -> UmbralMateriaRead` — devuelve umbral o default 60%
  - `upsert_umbral(materia_id, data, usuario) -> UmbralMateriaRead` — crea/actualiza umbral y dispara recálculo batch de `aprobado`

## 6. Routers y Endpoints

- [x] 6.1 Crear `app/api/v1/routers/calificaciones.py` con endpoints:
  - `POST /calificaciones/preview` (require_permission `calificaciones:importar`) — llama `CalificacionService.preview_import`
  - `POST /calificaciones/import` (require_permission `calificaciones:importar`) — llama `CalificacionService.confirm_import`
  - `POST /calificaciones/import-finalizacion` (require_permission `calificaciones:ver`) — llama `FinalizacionService.detectar_sin_corregir`
  - `DELETE /calificaciones/{materia_id}` (require_permission `calificaciones:vaciar`) — llama `CalificacionService.vaciar_materia`
- [x] 6.2 Crear `app/api/v1/routers/umbral.py` con endpoints:
  - `GET /umbral/{materia_id}` (require_permission `calificaciones:ver`) — llama `UmbralService.get_umbral`
  - `PUT /umbral/{materia_id}` (require_permission `calificaciones:importar`) — llama `UmbralService.upsert_umbral`

## 7. Wiring y Permisos

- [x] 7.1 Registrar routers en `app/main.py` (prefix `/api/v1`) + resolver conflictos de merge en main.py + fix bug `date` faltante en encuentros.py y guardias.py (C-13)
- [x] 7.2 Agregar permisos `calificaciones:importar`, `calificaciones:ver`, `calificaciones:vaciar` a la migración de seed de RBAC (o crear migración separada 008b si el seed ya está fijo) — asignar a roles PROFESOR y COORDINADOR según la KB
- [x] 7.3 Agregar dependencia `openpyxl` a `backend/pyproject.toml` (ya estaba presente)
