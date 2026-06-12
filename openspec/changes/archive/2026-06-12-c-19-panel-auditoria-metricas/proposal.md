## Why

C-05 dejó instalado el modelo `AuditLog` (E-AUD) append-only con su trigger DB y el helper `record_audit`. Hoy todos los módulos del sistema (C-06 a C-18) ya escriben en él, pero no existe ninguna superficie de lectura sobre esa información. Coordinación y administración necesitan visibilidad operativa: detectar docentes inactivos, ver el estado agregado de comunicaciones por docente, supervisar el volumen de uso por día y consultar el log completo de auditoría con filtros (F9.1, F9.2 — Épica 9 de la KB; FL-11). Sin C-19 el trail de auditoría existe pero es ilegible — no cumple su propósito.

Este change es **read-only sobre `AuditLog`** y sobre el modelo `Comunicacion` (C-12). No crea tablas nuevas, no escribe sobre auditoría (RN-23: registro inmutable) y no agrega permisos: `auditoria:ver` ya está seeded en C-04 (`ADMIN` global, `COORDINADOR (propio)`, `FINANZAS` global). Cumple [RN-23](../../../knowledge-base/05_reglas_de_negocio.md#rn-23) y [RN-24](../../../knowledge-base/05_reglas_de_negocio.md#rn-24) exponiendo los códigos cerrados del catálogo `AuditAction`.

## What Changes

- **Panel de interacciones** (F9.1): cuatro sub-vistas servidas por `/api/auditoria/panel/*`:
  - `GET /api/auditoria/panel/acciones-por-dia` — serie temporal (count por `DATE(fecha_hora)`) con filtros de rango.
  - `GET /api/auditoria/panel/comunicaciones-por-docente` — agregado de `Comunicacion.estado` agrupado por `actor_id` (usa el modelo `Comunicacion` de C-12, no escribe).
  - `GET /api/auditoria/panel/interacciones-por-docente-materia` — métricas de uso (count) por `(actor_id, materia_id, accion)` con desglose por categoría de acción.
  - `GET /api/auditoria/panel/ultimas-acciones` — log de últimas N acciones con N configurable (default 200, máx 1000) y filtros opcionales.
- **Log completo de auditoría** (F9.2, RN-23/RN-24): `GET /api/auditoria/log` paginado con filtros de rango de fechas, `materia_id`, `usuario_id` (actor o impersonado), `accion`, `estado` (resultado derivado del `detalle` cuando aplique). Paginación obligatoria (default `page_size=50`, máx `200`).
- **Códigos de acción** (`GET /api/auditoria/catalogo-acciones`): expone el enum `AuditAction` para que el frontend pueda renderizar selectores de filtro sin codear el catálogo (RN-24).
- **Guard único**: `require_permission("auditoria:ver")` en todos los endpoints. **Fail-closed**: sin permiso → 403.
- **Scope `(propio)` del coordinador** (RBAC fino, patrón ya consolidado en C-11): cuando `PermissionContext.is_propio == True` (COORDINADOR), el Service restringe TODOS los queries a `actor_id == current_user.id` o `impersonado_id == current_user.id`. ADMIN y FINANZAS ven el tenant completo.
- **Multi-tenancy**: todos los queries pasan por `AuditoriaPanelRepository(db_session, tenant_id)`, que extiende el patrón de `AuditLogRepository` con métodos de agregación de solo-lectura.
- **Sin migración Alembic**, sin nuevos modelos, sin tabla de cache. El cómputo es on-demand sobre `audit_log` (ya indexado por `tenant_id` y `fecha_hora`).

## Capabilities

### New Capabilities

- `auditoria-panel`: agregaciones operativas sobre `audit_log` para la épica 9 (F9.1). Cuatro endpoints de panel + endpoint de catálogo de códigos. Read-only, multi-tenant, RBAC con scope `(propio)`.
- `auditoria-log-query`: endpoint paginado de consulta del log completo de auditoría (F9.2) con filtros. Read-only. Scope `(propio)` para COORDINADOR. Cumple RN-23 (registro inmutable: no se expone ninguna operación de escritura) y RN-24 (filtros por código cerrado del catálogo).

### Modified Capabilities

- Ninguna. `audit-log-model` y `audit-action-helper` (C-05) no se modifican: este change los CONSUME en modo solo-lectura.

## Impact

- **Backend** (todos archivos nuevos, ningún modelo modificado):
  - `backend/app/repositories/auditoria_panel_repository.py` — agregaciones SELECT-only sobre `audit_log` + `comunicacion`. Sin INSERT/UPDATE/DELETE.
  - `backend/app/services/auditoria_panel_service.py` — orquesta filtros, aplica scope `(propio)` desde `PermissionContext`, delega al repository.
  - `backend/app/api/v1/routers/auditoria.py` — endpoints `/api/auditoria/*` con guard `require_permission("auditoria:ver")`.
  - `backend/app/schemas/auditoria.py` — DTOs Pydantic v2 (`extra='forbid'`): `AccionesPorDiaResponse`, `ComunicacionesPorDocenteResponse`, `InteraccionesPorDocenteMateriaResponse`, `UltimasAccionesResponse`, `AuditLogEntrySchema`, `AuditLogPageResponse`, `CatalogoAccionesResponse`, `AuditLogFiltrosQuery`.
  - `backend/app/main.py` — registrar `auditoria_router` con prefix `/api/auditoria` y tag `["auditoria"]`.
- **Migraciones**: ninguna. AuditLog y Comunicacion ya existen (C-05 y C-12).
- **RBAC**: ninguno nuevo. `auditoria:ver` ya está seeded (`002_create_rbac_tables.py`): COORDINADOR con `es_propio=True`, ADMIN y FINANZAS con `es_propio=False`.
- **Tests** (`backend/tests/test_auditoria_panel.py`):
  - Agregaciones: `acciones_por_dia` cuenta correctamente por día UTC; `comunicaciones_por_docente` agrupa por estado y actor; `interacciones_por_docente_materia` agrupa por `(actor_id, materia_id, accion)`; `ultimas_acciones` respeta `limit` configurable y default 200.
  - Filtros: rango de fechas (inclusive), materia, usuario (actor o impersonado), código de acción (rechaza códigos no presentes en `AuditAction`).
  - Paginación del log: defaults `page=1, page_size=50`; `page_size > 200` retorna 422.
  - Scope `(propio)`: COORDINADOR sólo ve registros donde `actor_id == self.id` O `impersonado_id == self.id`.
  - Aislamiento multi-tenant: Tenant B no aparece en queries de Tenant A.
  - RBAC: rol sin `auditoria:ver` recibe 403 en cualquier endpoint `/api/auditoria/*`.
  - Inmutabilidad (RN-23): no existe ningún método de escritura en el repository; el spec lo afirma a nivel de capacidad.
- **Governance**: nivel **ALTO**. Aunque el change es read-only sobre auditoría, expone toda la actividad histórica de un tenant. Requiere aprobación humana de proposal + design antes del apply. No se ejecuta build ni commit sin pedido explícito.
- **Dependencias**: C-05 ✓ (`AuditLog` modelo + helper + RBAC `auditoria:ver`), C-07 ✓ (`Usuario`, `Asignacion`), C-12 ✓ (`Comunicacion` con estados Pendiente/Enviando/Enviado/Error/Cancelado).
- **Desbloquea**: C-22 (frontend panel de auditoría) en GATE 11.

## Open Questions

- **OQ-1 — Categorización de acciones por "tipo de uso" en F9.1**: la KB pide métricas por "análisis de desempeño, vista previa, importación, envío, limpieza de datos, configuración de umbral, emails generados, lotes procesados". El catálogo actual `AuditAction` (28 códigos) no incluye una taxonomía oficial. **Decisión provisional**: agrupar por prefijo del código (`CALIFICACIONES_*`, `COMUNICACION_*`, `ASIGNACION_*`, `LIQUIDACION_*`, `IMPERSONACION_*`, `AVISO_*`, `TAREA_*`, `PROGRAMA_*`, `FECHA_*`, `PADRON_*`). El frontend renderiza esos prefijos como "categoría". Decisión revisable en C-22.
- **OQ-2 — "Estado" como filtro en F9.2**: la KB lista "estado" entre los filtros pero `AuditLog` no tiene campo de estado directo. Interpretación: cuando `accion == COMUNICACION_ENVIAR`, el "estado" se infiere del campo `detalle.estado` (JSONB) si está presente; en otros casos el filtro se ignora (devuelve todos). El spec hace explícito este contrato.
