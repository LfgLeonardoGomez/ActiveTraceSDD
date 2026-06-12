## Context

C-05 dejó la infraestructura de auditoría en su forma append-only canónica:

- Modelo `AuditLog` (`backend/app/models/audit_log.py`): tabla `audit_log` con `id`, `tenant_id`, `fecha_hora` (UTC), `actor_id`, `impersonado_id`, `materia_id`, `accion`, `detalle` (JSONB), `filas_afectadas`, `ip`, `user_agent`. Sin `updated_at` ni `deleted_at`. Trigger DB `trg_audit_log_immutable` rechaza UPDATE y DELETE (RN-23).
- Repository `AuditLogRepository`: scoped al tenant, expone `insert` y `list_by_tenant` (ordenado por `fecha_hora.desc()`).
- Helper `record_audit` + enum `AuditAction` (`backend/app/core/audit.py`): catálogo cerrado de 28 códigos `MODULO_ACCION` (RN-24).
- RBAC (C-04, migración `002_create_rbac_tables.py`): permiso `auditoria:ver` ya seeded:
  - `COORDINADOR` → `es_propio=True`
  - `ADMIN` → `es_propio=False`
  - `FINANZAS` → `es_propio=False`

Comunicaciones (C-12) ya escribió `Comunicacion.estado` (Pendiente / Enviando / Enviado / Error / Cancelado) y `Comunicacion.actor_id` por cada envío, por lo que el panel de comunicaciones por docente se sirve agregando ese modelo — no es necesario extraer información del `detalle` JSONB.

Este change es la PRIMERA superficie de lectura sobre el sistema de auditoría. No se modifica ningún archivo de C-05; sólo se agregan módulos `auditoria_*` que consumen los existentes.

## Goals / Non-Goals

**Goals:**
- Exponer el panel de F9.1 con cuatro agregaciones (acciones por día, comunicaciones por docente, interacciones por docente×materia, últimas acciones).
- Exponer el log completo (F9.2) paginado con filtros canónicos: rango fechas, materia, usuario, código de acción.
- Servir el catálogo cerrado de códigos (`AuditAction`) como endpoint, para que el frontend no duplique constantes (RN-24).
- Respetar scope `(propio)` del COORDINADOR de extremo a extremo (todas las queries del repository reciben `actor_filter`).
- Tests con DB real (sin mocks) que cubran agregaciones, filtros, scope `(propio)` y aislamiento tenant.

**Non-Goals:**
- **No** modificar `AuditLog`, `AuditLogRepository`, ni `record_audit` (C-05 sigue siendo source of truth).
- **No** crear ninguna entidad nueva (no hay migración Alembic).
- **No** persistir resultados agregados (sin caché, sin tabla snapshot).
- **No** implementar exportación (no está en F9.1/F9.2 como capability). Si surge en C-22, se agrega con un change posterior.
- **No** materializar vistas, ni triggers, ni jobs background.

## Decisions

### D-01 — Read-only contract enforced por el repositorio dedicado

**Decisión**: `AuditoriaPanelRepository` y `AuditoriaLogQueryRepository` exponen **solo** métodos `get_*` / `list_*` / `count_*`. No tienen `insert`, `update`, `delete`, `flush`, `add`, ni acceso al ORM más allá de `select(...)`.

**Rationale**: hace imposible (a nivel de superficie de API interna) que un futuro cambio rompa RN-23. La inmutabilidad sigue protegida por el trigger DB de C-05, pero la capa Repository agrega defensa en profundidad: ningún path de código que pase por `auditoria_*` puede escribir.

**Trade-off**: dos repositories en vez de extender `AuditLogRepository`. Se acepta porque mantiene la responsabilidad limpia (C-05 = insert; C-19 = read) y permite que `AuditLogRepository` siga siendo el writer canónico desde otros Services.

### D-02 — Dos repositories: panel vs log-query

**Decisión**: separar `AuditoriaPanelRepository` (agregaciones de F9.1: COUNT, GROUP BY) de `AuditoriaLogQueryRepository` (consulta paginada de F9.2). Comparten el constructor `(db_session, tenant_id)` y el `actor_filter` opcional.

**Rationale**: cada uno tiene una forma distinta de query (panel = `SELECT count(*), date_trunc(...)`; log = `SELECT * FROM audit_log WHERE ... LIMIT ... OFFSET`). Mezclarlos en un único repo deriva en métodos divergentes con poco en común. La división mantiene cada archivo bajo el budget de 500 LOC.

**Alternativa descartada**: un único `AuditoriaRepository` con todo. Se descartó por riesgo de explotar el budget de LOC.

### D-03 — Scope `(propio)` aplicado en el Service, no en el Router

**Decisión**: el Router pasa el `PermissionContext` y el `current_user` al Service. El Service decide:
```python
actor_filter = current_user.id if permission_ctx.is_propio else None
```
y lo propaga al Repository. Los Repositories aceptan `actor_filter: UUID | None`. Cuando no es `None`, agregan a la cláusula WHERE: `OR(actor_id == actor_filter, impersonado_id == actor_filter)`.

**Rationale**: replica exactamente el patrón de C-11 (`analisis_service.py`), C-13 y C-16. Mantiene el Router como puro mapeo HTTP→Service y deja la lógica de scope en una sola capa testeable.

**Importante**: el filtro incluye `OR impersonado_id == actor_filter` porque RN-41 indica que la atribución bajo impersonación va al actor real. Si el coordinador fue impersonado por un ADMIN, sus acciones aparecen con `actor_id = ADMIN` y `impersonado_id = COORDINADOR`. Para que el coordinador vea sus propias acciones (incluso si fueron ejecutadas durante una impersonación), se chequea ambos campos.

### D-04 — Categorización por prefijo del código de acción

**Decisión**: para las "interacciones por docente×materia" agrupadas por categoría (F9.1, métricas de uso por tipo), se calcula una categoría `categoria = accion.split("_")[0]` (e.g. `CALIFICACIONES_IMPORTAR` → `CALIFICACIONES`). El response incluye `accion` (código completo, exacto) y `categoria` (prefijo agrupador).

**Rationale**: el catálogo `AuditAction` ya está naming-convention `MODULO_ACCION` (RN-24); reutilizar el prefijo evita codear una tabla de mapping aparte. Es revisable en C-22 si el frontend quiere otro corte. Documentado como OQ-1.

**Trade-off**: si en el futuro se agrega un código como `MOD_MIS_EQUIPOS` (ejemplo de la KB con dos guiones), el split por `_` rompe la agrupación. Decisión: el spec exige que toda nueva entrada del enum mantenga `^[A-Z]+_[A-Z_]+$` con la categoría como primer segmento. C-05 ya respeta este invariante.

### D-05 — Filtro de "estado" en F9.2 vía `detalle.estado`

**Decisión**: cuando el filtro `estado` está presente en `GET /api/auditoria/log`, el WHERE agrega `detalle ->> 'estado' = :estado`. Si el campo no existe en el JSONB, el registro no matchea. El filtro no falla con error; simplemente acota.

**Rationale**: la KB lista "estado" como filtro pero `AuditLog` no tiene columna dedicada (RN-23 lo prohíbe — la tabla es inmutable, no se le agregan columnas). El uso documentado de `detalle` es contexto adicional; el contrato de C-12 (Comunicaciones) ya guarda `detalle = {"estado": "Enviado", ...}` cuando registra `COMUNICACION_ENVIAR`. Documentado en OQ-2.

**Trade-off**: la query usa un índice JSONB del tipo `gin` o `expression index`. Para el volumen esperado (~10k filas por día por tenant en peak) se acepta scan sin índice; si la performance degrada, se agrega `CREATE INDEX ... ON audit_log ((detalle->>'estado'))` en un change posterior. Mientras tanto, los filtros principales (rango de fechas + tenant) ya usan el índice existente `ix_audit_log_tenant` + el orden por `fecha_hora`.

### D-06 — Catálogo de acciones servido desde el enum

**Decisión**: `GET /api/auditoria/catalogo-acciones` retorna `[{codigo, categoria}]` derivado en runtime de `AuditAction` (`list(AuditAction)`). No se duplica en BD.

**Rationale**: respeta RN-24 (catálogo cerrado). El enum es la única fuente de verdad. Si se agrega un código a `AuditAction`, el endpoint lo expone automáticamente al frontend.

### D-07 — Paginación con bounds explícitos

**Decisión**:
- `GET /api/auditoria/log`: `page` default `1`, `page_size` default `50`, máximo `200`. Excedente → 422 (`Pydantic Field(le=200)`).
- `GET /api/auditoria/panel/ultimas-acciones`: `limit` default `200`, máximo `1000`. Excedente → 422.

**Rationale**: alineado con el patrón de C-11 (`page_size > 200` retorna 422). El máximo de `ultimas-acciones` es más alto porque la KB lo declara configurable; 1000 es el techo de seguridad para evitar payloads desproporcionados.

### D-08 — Sin tests con mocks de DB

**Decisión**: todos los tests de agregación usan la fixture de DB real (PostgreSQL en contenedor de test). Se siembran filas de `audit_log` directamente con `record_audit(...)` desde el setup.

**Rationale**: regla dura #4 del proyecto. Mockear agregaciones JSONB y `date_trunc` no prueba nada real.

## Risks / Trade-offs

- **[Riesgo] Performance del panel con datos históricos grandes** → Mitigación: todos los queries del panel exigen `fecha_desde` y `fecha_hasta` (default últimos 30 días si no se pasan); el índice existente `ix_audit_log_tenant` + el orden `fecha_hora.desc()` mantienen el escaneo acotado. Si en producción el volumen real degrada las queries, se agrega un índice compuesto `(tenant_id, fecha_hora DESC, accion)` en un change posterior. No es parte de este change.
- **[Riesgo] Categoría inferida del prefijo no coincide con la taxonomía esperada por el frontend** → Mitigación: documentado como OQ-1; cierre formal en C-22. El endpoint `/api/auditoria/catalogo-acciones` expone la categoría calculada para que el frontend la consuma tal cual.
- **[Riesgo] Filtro `usuario_id` ambiguo (actor real o impersonado)** → Decisión: el filtro busca por `OR(actor_id = X, impersonado_id = X)`. El response incluye ambos campos para que el consumer distinga. Documentado en el spec.
- **[Trade-off] Sin export de log** → Decisión consciente. Si surge la necesidad, se trata en C-22 o en un change posterior. El log paginado más el panel cubren el flujo FL-11 sin export.

## Migration Plan

Ninguna migración Alembic. El único requisito de deploy es que C-05 (audit_log) y C-12 (comunicacion) estén aplicados — ambos archivados.

## Open Questions

- **OQ-1 — Taxonomía oficial de categorías de acción**: ¿el frontend necesita una agrupación distinta a la inferida por prefijo del código? Cierre formal con C-22; provisional: prefijo del `AuditAction`.
- **OQ-2 — Semántica del filtro "estado" en el log completo**: el contrato actual (filtra por `detalle->>'estado'`) cubre `COMUNICACION_ENVIAR`. ¿Aplica también a otros códigos? Provisional: sí cuando exista; si el campo no está en `detalle`, el registro no matchea (silent skip). Revisable.
