## 1. Modelos y migración

- [x] 1.1 Crear `backend/app/models/evaluacion.py` con `Evaluacion` (materia_id, cohorte_id, tipo enum, instancia, dias_disponibles, cupo_por_dia), `ReservaEvaluacion` (evaluacion_id, alumno_id, fecha_hora, estado enum Activa/Cancelada) y `ResultadoEvaluacion` (evaluacion_id, alumno_id, nota_final texto); todos con BaseModelMixin
- [x] 1.2 Crear tabla asociativa `evaluacion_candidato` (evaluacion_id, alumno_id, PK compuesta) en el mismo modelo o como metadata Table
- [x] 1.3 Actualizar `backend/app/models/__init__.py` con los nuevos modelos y exportarlos en `__all__`
- [x] 1.4 Crear `backend/alembic/versions/010_evaluaciones.py`: tablas `evaluacion`, `evaluacion_candidato`, `reserva_evaluacion`, `resultado_evaluacion` + índices; seed de 3 permisos RBAC (`coloquios:gestionar`, `coloquios:reservar`, `coloquios:ver`) + asociaciones por rol

## 2. Schemas Pydantic

- [x] 2.1 Crear `backend/app/schemas/evaluacion.py` con schemas (todos `extra='forbid'`): `TipoEvaluacion` enum, `EvaluacionCreateSchema`, `EvaluacionUpdateSchema`, `EvaluacionResponseSchema` (incluye convocados, reservas_activas, cupos_libres_por_dia), `CandidatosImportSchema`, `ReservaCreateSchema`, `ReservaResponseSchema`, `ResultadoUpsertSchema`, `ResultadoResponseSchema`, `MetricasColoquiosSchema`, `AgendaResponseSchema`

## 3. Repository

- [x] 3.1 Crear `backend/app/repositories/evaluacion_repository.py` con `EvaluacionRepository(BaseRepository)` y métodos: `create`, `get_by_id`, `list_with_metrics` (query con counts JOIN), `update`, `import_candidatos` (upsert batch), `get_candidatos`, `is_candidato`
- [x] 3.2 Agregar `create_reserva` con `SELECT FOR UPDATE` para validar cupo antes del INSERT (D3 del design)
- [x] 3.3 Agregar `cancel_reserva`, `get_reservas`, `get_reserva_by_id`, `get_reserva_activa_del_alumno`
- [x] 3.4 Agregar `upsert_resultado`, `get_resultados_con_candidatos` (LEFT JOIN candidatos con resultado), `get_resultados_csv_rows`
- [x] 3.5 Agregar `get_metricas_globales`, `get_agenda_global` con filtros opcionales (evaluacion_id, fecha_desde, fecha_hasta, materia_id)

## 4. Service

- [x] 4.1 Crear `backend/app/services/evaluacion_service.py` con `EvaluacionService(db_session, tenant_id, usuario_id)` y métodos: `crear_convocatoria`, `importar_candidatos`, `list_convocatorias`, `update_convocatoria`
- [x] 4.2 Implementar `crear_reserva`: verificar candidato → contar cupo con FOR UPDATE → insertar (lanza 409 si sin cupo o duplicada)
- [x] 4.3 Implementar `cancelar_reserva`: verificar pertenencia o permiso gestionar → verificar estado Activa → cancelar
- [x] 4.4 Implementar `get_reservas`, `registrar_resultado` (upsert), `get_resultados`
- [x] 4.5 Implementar `get_metricas_globales`, `get_agenda_global`

## 5. Router y endpoints

- [x] 5.1 Crear `backend/app/api/v1/routers/coloquios.py` con todos los endpoints bajo `/api/coloquios/`:
  - `POST /` (gestionar)
  - `GET /` (ver)
  - `GET /metricas` (ver)
  - `GET /agenda` (gestionar)
  - `PATCH /{id}` (gestionar)
  - `POST /{id}/candidatos` (gestionar)
  - `GET /{id}/candidatos` (ver)
  - `POST /{id}/reservas` (reservar)
  - `GET /{id}/reservas` (ver)
  - `DELETE /{id}/reservas/{reserva_id}` (reservar o gestionar)
  - `POST /{id}/resultados` (gestionar)
  - `GET /{id}/resultados` (ver)
  - `GET /{id}/resultados/export` (ver, StreamingResponse CSV)
- [x] 5.2 Registrar `coloquios_router` en `backend/app/main.py`

## 6. Tests

- [x] 6.1 Crear `backend/tests/test_evaluaciones.py` con safety net: correr tests de rutas/schemas que no necesiten DB
- [x] 6.2 Test unitario: cupo lleno → `create_reserva` lanza 409
- [x] 6.3 Test unitario: reserva duplicada del mismo alumno → 409 `reserva_duplicada`
- [x] 6.4 Test unitario: cancelar reserva ya cancelada → 409 `reserva_ya_cancelada`
- [x] 6.5 Test unitario: alumno no candidato intenta reservar → 403
- [x] 6.6 Test de integración (DB): crear convocatoria → importar candidatos → reserva exitosa → cancel reserva → cupo liberado
- [x] 6.7 Test de integración: upsert resultado (crear + actualizar mismo alumno)
- [x] 6.8 Test de integración: métricas globales reflejan candidatos/reservas/resultados correctamente
- [x] 6.9 Test de integración: aislamiento multi-tenant (Tenant A no ve convocatorias del Tenant B)
- [x] 6.10 Test de integración: export CSV de resultados (formato y columnas correctas)
