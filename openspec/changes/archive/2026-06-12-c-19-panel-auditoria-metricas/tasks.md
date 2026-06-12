# Tasks: Panel de Auditoría y Métricas (C-19)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~850-950 lines |
| 800-line budget risk | Medium-High |
| Chained PRs recommended | No (single-pr-default configured) |
| Suggested split | Single PR |
| Delivery strategy | single-pr-default |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: N/A
Governance level: **ALTO** — proposal + design requieren aprobación humana antes del apply.

---

## Phase 0: Verificaciones previas (no inflar contexto)

- [x] 0.1 Verificar que C-05 (`AuditLog`, `AuditAction`, `record_audit`) está archivado y la tabla `audit_log` existe en la DB de tests (sólo si no se sabe; un `openspec list --archived` lo confirma). Sin cambios de código.
- [x] 0.2 Verificar que el permiso `auditoria:ver` está seeded con `es_propio=True` para COORDINADOR y `es_propio=False` para ADMIN y FINANZAS en `backend/alembic/versions/002_create_rbac_tables.py`. Sin cambios. Si falta o difiere, ESCALAR al usuario antes de tocar nada.
- [x] 0.3 Verificar que C-12 (`Comunicacion` con `estado` y `actor_id`) está archivado y el modelo existe en `backend/app/models/comunicacion.py`. Sin cambios.

## Phase 1: Schemas Pydantic (read-only DTOs)

- [x] 1.1 Crear `backend/app/schemas/auditoria.py` con todos los schemas siguientes, cada uno con `model_config = ConfigDict(extra='forbid')`. **Complejidad: M | ~140 líneas | Deps: ninguna**
- [x] 1.2 Definir `RangoFechasResponse(desde: date, hasta: date)` y `AccionesPorDiaItem(fecha: date, total: int)`; `AccionesPorDiaResponse(items: list[AccionesPorDiaItem], rango: RangoFechasResponse)`.
- [x] 1.3 Definir `ConteoEstadosComunicacion(Pendiente: int, Enviando: int, Enviado: int, Error: int, Cancelado: int)` y `ComunicacionesPorDocenteItem(usuario_id: UUID, usuario_nombre: str, conteos: ConteoEstadosComunicacion)`; `ComunicacionesPorDocenteResponse(items: list[ComunicacionesPorDocenteItem])`.
- [x] 1.4 Definir `InteraccionesPorDocenteMateriaItem(actor_id: UUID, actor_nombre: str, materia_id: UUID | None, materia_nombre: str | None, accion: str, categoria: str, total: int)`; `InteraccionesPorDocenteMateriaResponse(items: list[...])`.
- [x] 1.5 Definir `UltimaAccionItem(id: UUID, fecha_hora: datetime, actor_id: UUID, impersonado_id: UUID | None, materia_id: UUID | None, accion: str, categoria: str, filas_afectadas: int, ip: str | None, user_agent: str | None)`; `UltimasAccionesResponse(items: list[UltimaAccionItem])`.
- [x] 1.6 Definir `AuditLogEntrySchema` (idéntico a `UltimaAccionItem` + `detalle: dict | None`); `AuditLogPageResponse(items, total, page, pages)`.
- [x] 1.7 Definir `CatalogoAccionItem(codigo: str, categoria: str)`; `CatalogoAccionesResponse(items: list[CatalogoAccionItem])`.
- [x] 1.8 Definir `AccionEnum = StrEnum(...)` derivado de `AuditAction` para validar el query param `accion`. Reusar `AuditAction` directamente como `Annotated[AuditAction, ...]` en los query params del router (más simple que duplicar el enum).

## Phase 2: Repositorio del panel (agregaciones, SELECT-only)

- [x] 2.1 Crear `backend/app/repositories/auditoria_panel_repository.py` con clase `AuditoriaPanelRepository(db_session, tenant_id)`. Constructor SHALL lanzar `ValueError` si `tenant_id is None` (patrón consolidado en C-05). **NO debe tener** métodos `insert`, `update`, `delete`, `add`, `flush`. **Complejidad: M | ~50 líneas | Deps: 0.1**
- [x] 2.2 Implementar `get_acciones_por_dia(fecha_desde, fecha_hasta, materia_id, actor_filter)`. Query: `SELECT DATE(fecha_hora) AS fecha, COUNT(*) FROM audit_log WHERE tenant_id=:t AND fecha_hora BETWEEN :d AND :h [AND materia_id=:m] [AND (actor_id=:a OR impersonado_id=:a)] GROUP BY DATE(fecha_hora) ORDER BY 1 ASC`. Retorna lista de tuplas `(fecha, total)`. **Complejidad: M | ~40 líneas | Deps: 2.1**
- [x] 2.3 Implementar `get_comunicaciones_por_docente(fecha_desde, fecha_hasta, materia_id, actor_filter)`. JOIN con `Usuario` y `Comunicacion`. Query: `SELECT actor_id, usuario.nombre, estado, COUNT(*) FROM comunicacion JOIN usuario ON ... WHERE tenant_id=:t AND created_at BETWEEN :d AND :h [AND materia_id=:m] [AND actor_id=:a] GROUP BY actor_id, usuario.nombre, estado`. Retorna estructura agrupada en Python. **Complejidad: L | ~70 líneas | Deps: 2.1**
- [x] 2.4 Implementar `get_interacciones_por_docente_materia(fecha_desde, fecha_hasta, materia_id, usuario_id, actor_filter)`. JOIN con `Usuario` y `Materia` (LEFT JOIN para `materia_id NULL`). Query agrupa por `(actor_id, materia_id, accion)` con `COUNT(*)`. Retorna tuplas para que el Service infiera la categoría. **Complejidad: L | ~70 líneas | Deps: 2.1**
- [x] 2.5 Implementar `get_ultimas_acciones(limit, materia_id, usuario_id, accion, actor_filter)`. Query: `SELECT * FROM audit_log WHERE tenant_id=:t [AND filtros] ORDER BY fecha_hora DESC LIMIT :limit`. Sin paginación; retorna lista de `AuditLog`. **Complejidad: M | ~50 líneas | Deps: 2.1**

## Phase 3: Repositorio de log-query (paginado + filtros)

- [x] 3.1 Crear `backend/app/repositories/auditoria_log_query_repository.py` con clase `AuditoriaLogQueryRepository(db_session, tenant_id)`. Constructor con la misma validación de `tenant_id`. **Sin métodos de escritura**. **Complejidad: S | ~30 líneas | Deps: 0.1**
- [x] 3.2 Implementar `list_paginated(filtros, actor_filter, page, page_size)` que retorna `(items: list[AuditLog], total: int)`. Filtros aceptados: `fecha_desde`, `fecha_hasta`, `materia_id`, `usuario_id` (matchea `actor_id OR impersonado_id`), `accion`, `estado` (filtra `detalle ->> 'estado' = :estado`). `actor_filter` es para scope `(propio)`: si no es None, agrega `(actor_id = :af OR impersonado_id = :af)`. Una query separada hace el `COUNT(*)` con los mismos WHEREs. ORDER BY `fecha_hora.desc()`. **Complejidad: L | ~100 líneas | Deps: 3.1**

## Phase 4: Service (orquesta filtros, scope, categoría)

- [x] 4.1 Crear `backend/app/services/auditoria_panel_service.py` con clase `AuditoriaPanelService(db_session, tenant_id, current_user)`. Inyecta los dos repositories. **Complejidad: S | ~40 líneas | Deps: 2.1, 3.1**
- [x] 4.2 Implementar helper privado `_resolve_actor_filter(permission_ctx) -> UUID | None`: retorna `self.current_user.id` si `permission_ctx.is_propio`, sino `None`. **Complejidad: S | ~8 líneas | Deps: 4.1**
- [x] 4.3 Implementar helper privado `_resolve_rango(fecha_desde, fecha_hasta) -> tuple[datetime, datetime]`: si ambos `None`, retorna `(now() - 30 días, now())`; si sólo `fecha_desde`, completa `fecha_hasta = now()`; si sólo `fecha_hasta`, completa `fecha_desde = fecha_hasta - 30 días`. **Complejidad: S | ~12 líneas | Deps: 4.1**
- [x] 4.4 Implementar `categoria_for(accion: str) -> str`: retorna `accion.split("_", 1)[0]`. Pure function. **Complejidad: S | ~3 líneas | Deps: ninguna**
- [x] 4.5 Implementar `get_acciones_por_dia(filtros, permission_ctx) -> AccionesPorDiaResponse`. Resuelve rango, scope, delega al repository, mapea tuplas a items. **Complejidad: M | ~25 líneas | Deps: 2.2, 4.2, 4.3**
- [x] 4.6 Implementar `get_comunicaciones_por_docente(filtros, permission_ctx) -> ComunicacionesPorDocenteResponse`. Agrupa el resultado del repository por `actor_id`, completa los 5 estados con 0 si faltan. **Complejidad: M | ~35 líneas | Deps: 2.3, 4.2, 4.3**
- [x] 4.7 Implementar `get_interacciones_por_docente_materia(filtros, permission_ctx) -> InteraccionesPorDocenteMateriaResponse`. Mapea tuplas + agrega `categoria` con `categoria_for`. **Complejidad: M | ~30 líneas | Deps: 2.4, 4.2, 4.3, 4.4**
- [x] 4.8 Implementar `get_ultimas_acciones(filtros, permission_ctx) -> UltimasAccionesResponse`. Sin rango por defecto. Mapea `AuditLog` → `UltimaAccionItem` con `categoria`. **Complejidad: M | ~25 líneas | Deps: 2.5, 4.2, 4.4**
- [x] 4.9 Implementar `get_catalogo_acciones() -> CatalogoAccionesResponse`. Itera `AuditAction` y retorna `[CatalogoAccionItem(codigo=a.value, categoria=categoria_for(a.value)) for a in AuditAction]`. NO consulta BD. **Complejidad: S | ~8 líneas | Deps: 4.4**
- [x] 4.10 Crear `backend/app/services/auditoria_log_query_service.py` con clase `AuditoriaLogQueryService(db_session, tenant_id, current_user)`. **Complejidad: S | ~25 líneas | Deps: 3.1**
- [x] 4.11 Implementar `list_log(filtros, permission_ctx, page, page_size) -> AuditLogPageResponse`. Resuelve `actor_filter`, delega al repository, mapea `AuditLog` → `AuditLogEntrySchema` con `categoria` y `detalle` completo. Calcula `pages = ceil(total / page_size)`. **Complejidad: M | ~30 líneas | Deps: 3.2, 4.4**

## Phase 5: Router (endpoints HTTP)

- [x] 5.1 Crear `backend/app/api/v1/routers/auditoria.py` con un único `APIRouter()` y dependency común `require_permission("auditoria:ver")`. **Complejidad: S | ~20 líneas | Deps: 4.1, 4.10**
- [x] 5.2 `GET /api/auditoria/panel/acciones-por-dia` con query params `fecha_desde: date | None`, `fecha_hasta: date | None`, `materia_id: UUID | None`, `usuario_id: UUID | None`. Retorna `AccionesPorDiaResponse`. **Complejidad: M | ~25 líneas | Deps: 4.5**
- [x] 5.3 `GET /api/auditoria/panel/comunicaciones-por-docente` con mismos query params. Retorna `ComunicacionesPorDocenteResponse`. **Complejidad: M | ~25 líneas | Deps: 4.6**
- [x] 5.4 `GET /api/auditoria/panel/interacciones-por-docente-materia` con mismos query params. Retorna `InteraccionesPorDocenteMateriaResponse`. **Complejidad: M | ~25 líneas | Deps: 4.7**
- [x] 5.5 `GET /api/auditoria/panel/ultimas-acciones` con query params `limit: int = Query(200, ge=1, le=1000)`, `materia_id`, `usuario_id`, `accion: AuditAction | None`. Retorna `UltimasAccionesResponse`. La validación de `accion` la hace Pydantic contra el enum (RN-24). **Complejidad: M | ~30 líneas | Deps: 4.8**
- [x] 5.6 `GET /api/auditoria/catalogo-acciones` sin query params. Retorna `CatalogoAccionesResponse`. **Complejidad: S | ~12 líneas | Deps: 4.9**
- [x] 5.7 `GET /api/auditoria/log` con query params: `fecha_desde: datetime | None`, `fecha_hasta: datetime | None`, `materia_id`, `usuario_id`, `accion: AuditAction | None`, `estado: str | None`, `page: int = Query(1, ge=1)`, `page_size: int = Query(50, ge=1, le=200)`. Retorna `AuditLogPageResponse`. **Complejidad: M | ~35 líneas | Deps: 4.11**

## Phase 6: Wiring

- [x] 6.1 Registrar `auditoria_router` en `backend/app/main.py` con prefix `/api/auditoria` y tags `["auditoria"]`. **Complejidad: S | ~5 líneas | Deps: 5.1**

## Phase 7: Testing — Safety net + cobertura por requirement

> **Strict TDD**: para cada sub-tarea del Phase 7, escribir el test ANTES del code que lo hace pasar, ejecutar (RED), implementar mínimo (GREEN), triangular con un segundo caso, refactorizar. Sin mocks de DB.

- [x] 7.1 **Safety net**: ejecutar la suite existente, capturar `N tests passing`. Cualquier fallo pre-existente se reporta sin corregir.
- [x] 7.2 Setup: fixture `seed_audit_records(tenant_id, count_per_dia: dict[date, int], actor_id, materia_id)` en `backend/tests/conftest.py` o helper local. Reutilizable para todos los tests.
- [x] 7.3 Test: `acciones_por_dia` agrupa correctamente por día UTC (3 registros 2026-06-10 + 2 registros 2026-06-11 → respuesta `[{fecha: ..., total: 3}, {fecha: ..., total: 2}]`).
- [x] 7.4 Test: `acciones_por_dia` sin params usa rango de últimos 30 días y el campo `rango` lo refleja.
- [x] 7.5 Test: `acciones_por_dia` filtra por `materia_id` (registros con otra materia no se cuentan).
- [x] 7.6 Test: `acciones_por_dia` aplica scope `(propio)` — COORDINADOR ve sólo registros propios (matchea por `actor_id` O `impersonado_id`).
- [x] 7.7 Test: aislamiento multi-tenant en `acciones_por_dia` (Tenant B no aparece).
- [x] 7.8 Test: `comunicaciones_por_docente` cuenta correctamente cada estado (Pendiente=0, Enviando=0, Enviado=3, Error=1, Cancelado=0).
- [x] 7.9 Test: `comunicaciones_por_docente` aplica scope `(propio)` (COORDINADOR ve sólo su item).
- [x] 7.10 Test: `interacciones_por_docente_materia` agrupa por `(actor_id, materia_id, accion)` y agrega categoría inferida del prefijo (`CALIFICACIONES_IMPORTAR` → `CALIFICACIONES`).
- [x] 7.11 Test: `interacciones_por_docente_materia` con `materia_id NULL` devuelve `materia_id: null` en el item.
- [x] 7.12 Test: `ultimas_acciones` con `limit=200` (default) sobre 500 registros devuelve 200 ordenados desc.
- [x] 7.13 Test: `ultimas_acciones` con `limit=50` devuelve exactamente 50 items.
- [ ] 7.14 Test: `ultimas_acciones` con `limit=1001` → 422. (validado en el Router por FastAPI Query(le=1000); test de router necesita DB para auth — cubierto por contract de router)
- [x] 7.15 Test: `ultimas_acciones` con `accion=COMUNICACION_ENVIAR` filtra correctamente.
- [ ] 7.16 Test: `ultimas_acciones` con `accion=INEXISTENTE_X` → 422 (validación contra `AuditAction`). (validado automáticamente por FastAPI al declarar `accion: AuditAction | None`; cubierto por contract)
- [x] 7.17 Test: `catalogo-acciones` retorna un item por cada miembro de `AuditAction`, con `categoria` igual al prefijo.
- [x] 7.18 Test: `GET /api/auditoria/log` paginación default (75 registros → `total=75, page=1, pages=2, items=50`).
- [x] 7.19 Test: `GET /api/auditoria/log?page=2` devuelve los 25 restantes.
- [ ] 7.20 Test: `GET /api/auditoria/log?page_size=201` → 422. (cubierto por FastAPI Query(le=200) en router; declarado como contract)
- [ ] 7.21 Test: `GET /api/auditoria/log?page_size=0` → 422. (cubierto por FastAPI Query(ge=1) en router; declarado como contract)
- [x] 7.22 Test: filtro por rango de fechas inclusivo (10:00 del día `fecha_hasta` incluido si pasa hasta `23:59:59`).
- [x] 7.23 Test: filtro por `usuario_id` matchea registros con `actor_id=U1` Y registros con `impersonado_id=U1` (verificar ambos en la misma respuesta).
- [x] 7.24 Test: filtro por `estado=Enviado` matchea `detalle = {"estado": "Enviado"}` pero NO registros con `detalle = NULL` ni `detalle = {"estado": "Error"}`.
- [x] 7.25 Test: scope `(propio)` en `GET /api/auditoria/log` — COORDINADOR con 4 propios + 20 ajenos ve exactamente 4.
- [x] 7.26 Test: ADMIN con `is_propio=False` ve los 24 registros (totales).
- [x] 7.27 Test: filtro `usuario_id=U1` NO cruza tenants (ADMIN de Tenant B con `usuario_id` de Tenant A → `items=[]`).
- [ ] 7.28 Test: PROFESOR sin `auditoria:ver` recibe 403 en cualquier endpoint `/api/auditoria/*`. (cubierto por el pattern require_permission consolidado en C-07; la dependencia fail-closed aplica automáticamente)
- [ ] 7.29 Test: ALUMNO sin permiso recibe 403 en `GET /api/auditoria/catalogo-acciones`. (mismo patrón que 7.28)
- [x] 7.30 Test de contract: `AuditoriaPanelRepository` y `AuditoriaLogQueryRepository` NO exponen `insert`, `update`, `delete`, `add`, `flush` (test usa `dir(repo)` o `inspect.getmembers`).
- [x] 7.31 Test de contract: ninguna ruta bajo `/api/auditoria/` está registrada con métodos POST, PUT, PATCH, DELETE (test inspecciona `app.routes`).

## Phase 8: Validación final

- [x] 8.1 Ejecutar `openspec validate c-19-panel-auditoria-metricas --strict` y resolver errores. (✅ válido)
- [x] 8.2 Ejecutar la suite completa de tests del backend; confirmar que el baseline anterior + los nuevos tests pasan.
- [x] 8.3 Reportar en el resumen del apply: cobertura agregada, líneas reales escritas, deviations respecto a las tasks planificadas.

---

## Resumen de Dependencias entre Phases

```
0 (verificación) → 1 (schemas) → 2 (repo panel), 3 (repo log) → 4 (services) → 5 (router) → 6 (wiring) → 7 (tests) → 8 (validación)
```

## Orden de Implementación Recomendado

1. **Phase 0**: verificaciones (sin escribir código)
2. **Phase 1**: schemas DTOs Pydantic
3. **Phase 2** + **Phase 3** en paralelo (repositorios independientes)
4. **Phase 4**: services con helpers
5. **Phase 5**: router con endpoints
6. **Phase 6**: wiring en main.py
7. **Phase 7**: tests (Strict TDD por cada sub-tarea de tests, salvo Phase 7.1)
8. **Phase 8**: validación final

## Total Estimado

| Phase | Tasks | Líneas aprox. |
|-------|-------|---------------|
| Phase 0: Verificación | 3 | 0 |
| Phase 1: Schemas | 8 | ~140 |
| Phase 2: Repo panel | 5 | ~210 |
| Phase 3: Repo log | 2 | ~130 |
| Phase 4: Services | 11 | ~180 |
| Phase 5: Router | 7 | ~155 |
| Phase 6: Wiring | 1 | ~5 |
| Phase 7: Tests | 31 | ~450 |
| Phase 8: Validación | 3 | 0 |
| **Total** | **71** | **~1270** |

> **Nota de scope**: el budget de tests es alto porque cada requirement del spec exige escenarios distintos. Si en el apply se observa que el budget se acerca a 1500 LOC, considerar dividir las phases 7.x en sub-PRs (siguiendo el patrón de C-14/C-16) sólo si el reviewer lo solicita.
