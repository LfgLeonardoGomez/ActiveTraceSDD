# Tasks: Avisos y Acknowledgment (C-15)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~950-1050 lines |
| 800-line budget risk | Medium-High |
| Chained PRs recommended | No (single-pr-default configured) |
| Suggested split | Single PR (user opted for 800-line budget) |
| Delivery strategy | single-pr-default |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: N/A
400-line budget risk: Medium-High (within 800-line configured budget)

---

## Phase 1: Foundation — Models + Migration

- [x] 1.1 Crear `backend/app/models/aviso.py` con `AlcanceAviso` (Global/PorMateria/PorCohorte/PorRol), `SeveridadAviso` (Info/Advertencia/Crítico), modelo `Aviso` (alcance, materia_id, cohorte_id, rol_destino, severidad, titulo, cuerpo, inicio_en, fin_en, orden, activo, requiere_ack) y `AcknowledgmentAviso` (aviso_id, usuario_id, confirmado_at); ambos con BaseModelMixin. **Complejidad: M | ~80 líneas | Deps: ninguna**
- [x] 1.2 Actualizar `backend/app/models/__init__.py` importando y exportando `Aviso`, `AcknowledgmentAviso`, `AlcanceAviso`, `SeveridadAviso` en `__all__`. **Complejidad: S | ~10 líneas | Deps: 1.1**
- [x] 1.3 Crear `backend/alembic/versions/011_aviso_acknowledgment.py`: tablas `aviso` y `acknowledgment_aviso` + índices (`ix_aviso_tenant`, `ix_aviso_tenant_activo_vigencia`, `ix_aviso_alcance`, `uq_ack_aviso_usuario`, `ix_ack_aviso_aviso`, `ix_ack_aviso_usuario`). **Complejidad: M | ~70 líneas | Deps: 1.1**

## Phase 2: Schemas Pydantic

- [x] 2.1 Crear `backend/app/schemas/aviso.py` con schemas (todos `extra='forbid'`): `AlcanceAviso`, `SeveridadAviso` (StrEnum), `AvisoCreateSchema`, `AvisoUpdateSchema`, `AvisoResponseSchema` (incluye created_at, updated_at), `AvisoListResponseSchema` (paginado: items, total, page, pages). **Complejidad: M | ~60 líneas | Deps: 1.1**
- [x] 2.2 Agregar `AvisoParaUsuarioSchema` (aviso + flag `acknowledged: bool`) y `AcknowledgmentResponseSchema` (id, aviso_id, usuario_id, confirmado_at, created_at) al mismo archivo. **Complejidad: S | ~25 líneas | Deps: 2.1**

## Phase 3: Repository — Data Access

- [x] 3.1 Crear `backend/app/repositories/aviso_repository.py` con `AvisoRepository(db_session, tenant_id)` y métodos CRUD: `create`, `get_by_id`, `list_avisos` (filtros: alcance, activo, severidad, paginación), `update`, `soft_delete`. **Complejidad: M | ~80 líneas | Deps: 1.1**
- [x] 3.2 Implementar `list_para_usuario(usuario_id, now)` con audience query (RN-20): EXISTS subqueries contra `Asignacion` para matching por alcance (Global/PorRol/PorMateria/PorCohorte), filtro de vigencia (RN-18: inicio_en <= now <= fin_en), flag `acknowledged` via EXISTS sobre `AcknowledgmentAviso`. **Complejidad: L | ~90 líneas | Deps: 3.1**
- [x] 3.3 Implementar `acknowledge(aviso_id, usuario_id)` + `get_acknowledgment(aviso_id, usuario_id)` para verificar existencia previa (409 en el service si duplicado). **Complejidad: M | ~40 líneas | Deps: 3.1**

## Phase 4: Service — Business Logic

- [x] 4.1 Crear `backend/app/services/aviso_service.py` con `AvisoService(db_session, tenant_id, usuario_id)` y métodos: `crear_aviso`, `get_aviso`, `list_avisos`, `update_aviso`, `delete_aviso`; cada método de escritura llama `record_audit` con `AVISO_CREAR`, `AVISO_ACTUALIZAR`, `AVISO_ELIMINAR` según corresponda. **Complejidad: M | ~70 líneas | Deps: 3.1, 2.1**
- [x] 4.2 Implementar `list_mis_avisos()`: delega a `repository.list_para_usuario()`, retorna solo avisos no acknowledged (RN-19). **Complejidad: S | ~20 líneas | Deps: 3.2, 4.1**
- [x] 4.3 Implementar `confirmar_aviso(aviso_id)`: verificar aviso visible (activo, no deleted, en vigencia), verificar no acknowledged previamente (409 si duplicado), crear acknowledgment, llamar `record_audit(AVISO_CONFIRMAR)`. **Complejidad: M | ~50 líneas | Deps: 3.3, 4.1**

## Phase 5: Router — API Endpoints

- [x] 5.1 Crear `backend/app/api/v1/routers/avisos.py` con endpoints:
  - `POST /api/avisos` → `require_permission("avisos:publicar")` → `service.crear_aviso()`
  - `GET /api/avisos` → `require_permission("avisos:publicar")` → `service.list_avisos()`
  - `GET /api/avisos/{id}` → `require_permission("avisos:publicar")` → `service.get_aviso()`
  - `PATCH /api/avisos/{id}` → `require_permission("avisos:publicar")` → `service.update_aviso()`
  - `DELETE /api/avisos/{id}` → `require_permission("avisos:publicar")` → `service.delete_aviso()`
  - `GET /api/avisos/mis-avisos` → `require_permission("avisos:confirmar")` → `service.list_mis_avisos()`
  - `POST /api/avisos/{id}/confirmar` → `require_permission("avisos:confirmar")` → `service.confirmar_aviso()`

  **Complejidad: L | ~120 líneas | Deps: 4.1, 4.2, 4.3, 2.1, 2.2**

## Phase 6: Wiring + Audit Codes

- [x] 6.1 Actualizar `backend/app/core/audit.py` agregando `AVISO_CREAR`, `AVISO_ACTUALIZAR`, `AVISO_ELIMINAR`, `AVISO_CONFIRMAR` al enum `AuditAction`. **Nota**: se agregaron 4 códigos separados (crear/actualizar/eliminar/confirmar) en lugar de `AVISO_PUBLICAR` para granularidad de auditoría. **Complejidad: S | ~3 líneas | Deps: ninguna**
- [x] 6.2 Registrar `avisos_router` en `backend/app/main.py` con prefix `/api/avisos` y tags `["avisos"]`. **Complejidad: S | ~5 líneas | Deps: 5.1**

## Phase 7: Testing

- [ ] 7.1 Crear `backend/tests/test_avisos.py` con tests unitarios: validación de schemas (extra='forbid' rechaza campos desconocidos), service mockeado para vigency validation (RN-18). **Complejidad: M | ~60 líneas | Deps: 2.1, 4.1**
- [ ] 7.2 Tests de integración (DB real): CRUD completo (create → get → update → delete), aislamiento multi-tenant (Tenant A no ve avisos de Tenant B). **Complejidad: M | ~80 líneas | Deps: 3.1, 4.1**
- [ ] 7.3 Tests de integración: audience query (RN-20) — Global visible para todos, PorRol matching/no-matching, PorMateria matching, PorCohorte matching, aviso fuera de vigencia no visible. **Complejidad: L | ~100 líneas | Deps: 3.2, 4.2**
- [ ] 7.4 Tests de integración: acknowledgment — confirmar aviso visible (200), confirmar aviso ya acknowledged (409), confirmar aviso fuera de vigencia (404), ack hace que aviso desaparezca de mis-avisos (RN-19). **Complejidad: M | ~70 líneas | Deps: 3.3, 4.3**
- [ ] 7.5 Tests de integración: RBAC — ALUMNO sin `avisos:publicar` recibe 403 en POST/GET/PATCH/DELETE /api/avisos; todos los roles con `avisos:confirmar` pueden acceder a mis-avisos y confirmar. **Complejidad: S | ~40 líneas | Deps: 5.1**

---

## Resumen de Dependencias

```
1.1 → 1.2, 1.3, 2.1, 3.1
1.3 → (migration standalone)
2.1 → 2.2, 4.1
3.1 → 3.2, 3.3, 4.1
3.2 → 4.2
3.3 → 4.3
4.1 → 4.2, 4.3, 5.1
4.2 → 5.1
4.3 → 5.1
5.1 → 6.2, 7.5
6.1 → (audit codes, no deps)
```

## Orden de Implementación Recomendado

1. **Phase 1** (Foundation): modelos + migration — base para todo lo demás
2. **Phase 6.1** (Audit codes): rápido, sin dependencias
3. **Phase 2** (Schemas): DTOs para service/router
4. **Phase 3** (Repository): data access con audience query
5. **Phase 4** (Service): business logic (RN-18/19/20)
6. **Phase 5** (Router): API endpoints
7. **Phase 6.2** (Wiring): registrar router en main.py
8. **Phase 7** (Testing): validar todo el flujo

---

## Total Estimado

| Phase | Tasks | Líneas aprox. |
|-------|-------|---------------|
| Phase 1: Foundation | 3 | ~160 |
| Phase 2: Schemas | 2 | ~85 |
| Phase 3: Repository | 3 | ~210 |
| Phase 4: Service | 3 | ~140 |
| Phase 5: Router | 1 | ~120 |
| Phase 6: Wiring + Audit | 2 | ~8 |
| Phase 7: Testing | 5 | ~350 |
| **Total** | **19** | **~1073** |
