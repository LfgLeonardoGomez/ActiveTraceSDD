## 1. Prerequisitos y estructura

- [x] 1.1 Verificar que el permiso `atrasados:ver` existe en tabla `Permiso`; si no existe, agregarlo con script de datos en `backend/app/core/seed_rbac.py` y asignarlo a roles TUTOR, PROFESOR, COORDINADOR, ADMIN
- [x] 1.2 Crear estructura de directorios: `backend/app/routers/analisis.py`, `backend/app/services/analisis_service.py`, `backend/app/repositories/analisis_repository.py`, `backend/app/schemas/analisis.py`
- [x] 1.3 Registrar el router `analisis` en `backend/app/main.py` con prefijo `/api/analisis`

## 2. Schemas Pydantic

- [x] 2.1 Definir `AlumnoAtrasadoSchema` con campos: `entrada_padron_id`, `alumno_nombre`, `alumno_email`, `motivo` (enum: `sin_datos` | `nota_insuficiente` | `actividades_faltantes`), `actividades_faltantes_count`, `actividades_reprobadas_count`
- [x] 2.2 Definir `AtrasadosResponseSchema` (lista paginada): `items: list[AlumnoAtrasadoSchema]`, `total`, `page`, `pages`
- [x] 2.3 Definir `RankingItemSchema`: `posicion`, `entrada_padron_id`, `alumno_nombre`, `actividades_aprobadas`; y `RankingResponseSchema` (lista completa, sin paginación)
- [x] 2.4 Definir `ReporteRapidoSchema`: `total_alumnos`, `total_actividades`, `con_aprobadas`, `atrasados`, `pct_aprobacion`, `sin_datos: bool`
- [x] 2.5 Definir `NotaFinalItemSchema`: `entrada_padron_id`, `alumno_nombre`, `alumno_email`, `nota_final: float | None`
- [x] 2.6 Definir `MonitorItemSchema`: `entrada_padron_id`, `alumno_nombre`, `email`, `materia_id`, `materia_nombre`, `actividades_aprobadas`, `actividades_totales`, `estado` (enum: `al_dia` | `atrasado` | `sin_datos`)
- [x] 2.7 Definir `MonitorResponseSchema` paginado: `items: list[MonitorItemSchema]`, `total`, `page`, `pages`
- [x] 2.8 Agregar `model_config = ConfigDict(extra='forbid')` en todos los schemas

## 3. Repository

- [x] 3.1 Implementar `AnalisisRepository.get_entradas_con_calificaciones(tenant_id, asignacion_id)` → retorna `EntradaPadron` activas + sus `Calificacion` (JOIN); filtra por tenant
- [x] 3.2 Implementar `AnalisisRepository.get_atrasados(tenant_id, asignacion_id, page, page_size)` → query paginada de alumnos atrasados (condición RN-06 en SQL: `aprobado = False` o sin calificación); retorna tupla `(items, total)`
- [x] 3.3 Implementar `AnalisisRepository.get_ranking(tenant_id, asignacion_id)` → COUNT de `aprobado = True` por alumno, ORDER BY desc, solo alumnos con al menos 1 (RN-09)
- [x] 3.4 Implementar `AnalisisRepository.get_metricas_rapidas(tenant_id, asignacion_id)` → un solo query con agregaciones COUNT para totales
- [x] 3.5 Implementar `AnalisisRepository.get_notas_finales(tenant_id, asignacion_id, actividad_ids)` → AVG de `nota_numerica` sobre actividades seleccionadas por alumno; actividades sin nota cuentan como 0.0
- [x] 3.6 Implementar `AnalisisRepository.get_tps_sin_corregir(tenant_id, asignacion_id)` → cruce de `EntradaPadron` con finalizaciones registradas sin `nota_textual` (RN-07/08, solo escala textual)
- [x] 3.7 Implementar `AnalisisRepository.get_monitor_general(tenant_id, filtros, page, page_size)` → query multi-asignación con filtros dinámicos (materia, regional, comisión, alumno, estado)
- [x] 3.8 Implementar `AnalisisRepository.get_monitor_propio(tenant_id, usuario_id, filtros, page, page_size)` → igual que general pero filtrado a asignaciones del usuario autenticado
- [x] 3.9 Implementar `AnalisisRepository.get_monitor_global(tenant_id, filtros, fecha_desde, fecha_hasta, page, page_size)` → extiende general con filtro de rango de fechas sobre `Calificacion.created_at`

## 4. Service — Motor de análisis

- [x] 4.1 Implementar `AnalisisService.get_atrasados(asignacion_id, permission_ctx, page, page_size)` → valida scope (is_propio: verifica titularidad), delega a repository, retorna `AtrasadosResponseSchema`
- [x] 4.2 Implementar `AnalisisService.get_ranking(asignacion_id, permission_ctx)` → valida scope, delega a repository, construye ranking con posiciones (manejo de empates + desempate alfabético), retorna `RankingResponseSchema`
- [x] 4.3 Implementar `AnalisisService.get_reporte_rapido(asignacion_id, permission_ctx)` → valida scope, llama `get_metricas_rapidas`, calcula `pct_aprobacion`, retorna `ReporteRapidoSchema`
- [x] 4.4 Implementar `AnalisisService.get_notas_finales(asignacion_id, actividad_ids, permission_ctx)` → valida que haya actividades numéricas en la selección (422 si no), delega a repository, retorna lista de `NotaFinalItemSchema`
- [x] 4.5 Implementar `AnalisisService.get_tps_sin_corregir(asignacion_id, permission_ctx)` → valida scope, delega a repository, retorna lista de items para export
- [x] 4.6 Implementar `AnalisisService.get_monitor_general(filtros, permission_ctx, page, page_size)` → verifica que el rol NO tenga `is_propio` (403 si tiene), delega a repository
- [x] 4.7 Implementar `AnalisisService.get_monitor_propio(filtros, permission_ctx, page, page_size)` → extrae `usuario_id` de permission_ctx, delega a repository
- [x] 4.8 Implementar `AnalisisService.get_monitor_global(filtros, fecha_desde, fecha_hasta, permission_ctx, page, page_size)` → igual que general + rango fechas; 403 si `is_propio`

## 5. Router — Endpoints

- [x] 5.1 `GET /api/analisis/atrasados` → guard `require_permission("atrasados:ver")`, query params `asignacion_id` (requerido), `page`, `page_size`; llama service; retorna `AtrasadosResponseSchema`
- [x] 5.2 `GET /api/analisis/ranking` → guard `atrasados:ver`, query params `asignacion_id` (requerido); llama service; retorna `RankingResponseSchema`
- [x] 5.3 `GET /api/analisis/reporte-rapido` → guard `atrasados:ver`, query param `asignacion_id`; retorna `ReporteRapidoSchema`
- [x] 5.4 `GET /api/analisis/notas-finales` → guard `atrasados:ver`, query params `asignacion_id`, `actividades` (lista de UUIDs); retorna lista de `NotaFinalItemSchema`
- [x] 5.5 `GET /api/analisis/notas-finales/export` → guard `atrasados:ver`, mismos params; retorna `StreamingResponse` CSV con `Content-Disposition: attachment; filename="notas_finales_<materia>.csv"`
- [x] 5.6 `GET /api/analisis/tps-sin-corregir/export` → guard `atrasados:ver`, query param `asignacion_id`; retorna `StreamingResponse` CSV; header `X-Sin-Datos-Finalizacion: true` si no hay datos
- [x] 5.7 `GET /api/analisis/monitor/general` → guard `atrasados:ver`, query params opcionales (`materia_id`, `regional`, `comision`, `alumno`, `estado_actividad`, `criterio_clasificacion`, `page`, `page_size`); retorna `MonitorResponseSchema`
- [x] 5.8 `GET /api/analisis/monitor/general/export` → guard `atrasados:ver`, mismos filtros opcionales; retorna `StreamingResponse` CSV sin límite de paginación
- [x] 5.9 `GET /api/analisis/monitor/propio` → guard `atrasados:ver`, query params opcionales (`alumno`, `email`, `comision`, `regional`, `actividad_id`, `min_actividades_cumplidas`, `page`, `page_size`); retorna `MonitorResponseSchema`
- [x] 5.10 `GET /api/analisis/monitor/global` → guard `atrasados:ver`, mismos params que general + `fecha_desde`, `fecha_hasta`; retorna `MonitorResponseSchema`

## 6. Tests — Safety net + TDD

- [x] 6.1 Verificar baseline: correr suite existente, capturar `N tests passing` antes de cualquier cambio
- [x] 6.2 Test: alumno sin calificaciones → aparece en atrasados con motivo `sin_datos`
- [x] 6.3 Test: alumno con `aprobado=False` → aparece en atrasados con motivo `nota_insuficiente`
- [x] 6.4 Test: alumno con todas las actividades aprobadas → NO aparece en atrasados
- [x] 6.5 Test: aislamiento multi-tenant en atrasados (Tenant B no ve datos de Tenant A)
- [x] 6.6 Test: PROFESOR intenta ver atrasados de asignación ajena → 403
- [x] 6.7 Test: COORDINADOR puede ver atrasados de cualquier asignación del tenant
- [x] 6.8 Test: usuario sin `atrasados:ver` → 403 en cualquier endpoint `/api/analisis/`
- [x] 6.9 Test: ranking excluye alumnos sin actividades aprobadas (RN-09)
- [x] 6.10 Test: ranking ordenado descendente; empate desempata por apellido
- [x] 6.11 Test: reporte rápido devuelve `sin_datos=true` cuando no hay calificaciones
- [x] 6.12 Test: notas finales — alumno sin nota en actividad seleccionada cuenta como 0.0
- [x] 6.13 Test: notas finales — 422 si selección no incluye actividades numéricas
- [x] 6.14 Test: export CSV de notas finales tiene encabezados correctos y ContentDisposition
- [x] 6.15 Test: export TPs sin corregir — actividades numéricas NO aparecen (RN-08)
- [x] 6.16 Test: export TPs sin corregir — sin datos de finalización devuelve CSV vacío + header `X-Sin-Datos-Finalizacion`
- [x] 6.17 Test: monitor general — filtro por `estado_actividad=atrasado` devuelve solo atrasados
- [x] 6.18 Test: monitor general — PROFESOR recibe 403
- [x] 6.19 Test: monitor propio — TUTOR solo ve sus propios alumnos, no los de otros docentes
- [x] 6.20 Test: monitor global — filtro por rango fechas acota calificaciones evaluadas
- [x] 6.21 Test: paginación — `page_size=200` devuelve 422
- [x] 6.22 Test: paginación — sin params usa defaults `page=1, page_size=50`, retorna metadatos `total/page/pages`
