## 1. Prerequisitos y schema

- [x] 1.1 Verificar que los permisos `comunicacion:enviar` y `comunicacion:aprobar` existen en seed RBAC; agregar si faltan, asignando `comunicacion:enviar` a TUTOR/PROFESOR/COORDINADOR/ADMIN y `comunicacion:aprobar` a COORDINADOR/ADMIN
- [x] 1.2 Agregar campo `requiere_aprobacion_comunicaciones: bool = False` al modelo `Tenant` en `backend/app/models/tenant.py` con `server_default='false'`
- [x] 1.3 Crear modelo `Comunicacion` en `backend/app/models/comunicacion.py` con todos los campos de E-21 más `aprobado: bool = False` y `error_detalle: str | None`; extender `BaseModelMixin` (tenant_id, soft delete)
- [x] 1.4 Generar migración Alembic `alembic revision --autogenerate -m "comunicacion"` y verificar que incluye tabla `comunicacion` y columna `requiere_aprobacion_comunicaciones` en `tenant`
- [x] 1.5 Registrar `Comunicacion` en `backend/app/models/__init__.py`

## 2. Integración N8N

- [x] 2.1 Crear `backend/app/integrations/n8n_client.py` con clase `N8NClient(webhook_url: str, timeout: int = 10)` y método async `send(destinatario: str, asunto: str, cuerpo: str) -> None`; lanza `N8NTimeoutError` en timeout y `N8NError` en error HTTP
- [x] 2.2 Agregar `N8N_WEBHOOK_URL` y `N8N_TIMEOUT_SECONDS` a `backend/app/core/config.py` (Settings); `N8N_WEBHOOK_URL` opcional (None por defecto); agregar a `.env.example`

## 3. Schemas Pydantic

- [x] 3.1 Definir `ComunicacionPreviewRequestSchema`: `destinatarios: list[DestinatarioSchema]`, `plantilla_asunto: str`, `plantilla_cuerpo: str`; `DestinatarioSchema`: `alumno_id: UUID`, `nombre: str`, `email: str`
- [x] 3.2 Definir `ComunicacionPreviewItemSchema`: `alumno_id`, `asunto_renderizado`, `cuerpo_renderizado`
- [x] 3.3 Definir `ComunicacionLoteRequestSchema`: `destinatarios: list[DestinatarioSchema]`, `plantilla_asunto`, `plantilla_cuerpo`, `materia_id: UUID`
- [x] 3.4 Definir `ComunicacionLoteResponseSchema`: `lote_id: UUID`, `total_encolados: int`, `requiere_aprobacion: bool`
- [x] 3.5 Definir `LoteEstadoSchema`: `lote_id`, `total`, `pendiente`, `enviando`, `enviado`, `error`, `cancelado`
- [x] 3.6 Agregar `model_config = ConfigDict(extra='forbid')` en todos los schemas

## 4. Repository

- [x] 4.1 Crear `ComunicacionRepository` en `backend/app/repositories/comunicacion_repository.py` extendiendo `BaseRepository` con scope de tenant
- [x] 4.2 Implementar `crear_lote(lote: list[dict], tenant_id, usuario_id, materia_id) -> UUID` → inserta N registros con el mismo `lote_id`, cifra `destinatario`, retorna `lote_id`
- [x] 4.3 Implementar `get_estado_lote(lote_id, tenant_id) -> dict` → COUNT por estado para el lote
- [x] 4.4 Implementar `aprobar_lote(lote_id, tenant_id) -> int` → UPDATE `aprobado=True` para todos los `Pendiente` del lote; retorna filas afectadas
- [x] 4.5 Implementar `cancelar_lote(lote_id, tenant_id) -> int` → UPDATE `estado=Cancelado` para todos los `Pendiente` del lote
- [x] 4.6 Implementar `cancelar_uno(comunicacion_id, tenant_id) -> Comunicacion` → transiciona a `Cancelado`; lanza error si estado no es `Pendiente`
- [x] 4.7 Implementar `retry_uno(comunicacion_id, tenant_id) -> Comunicacion` → transiciona de `Error` a `Pendiente`; lanza error si estado no es `Error`
- [x] 4.8 Implementar `get_pendientes_para_despacho(tenant_id, batch_size) -> list[Comunicacion]` → SELECT con filtro de estado `Pendiente` y `aprobado=True` (o tenant sin aprobación); ORDER BY `created_at` ASC; LIMIT `batch_size`
- [x] 4.9 Implementar `get_todos_pendientes_elegibles(batch_size) → list[Comunicacion]` → igual que 4.8 pero sin filtro de tenant (para el worker que procesa todos los tenants)
- [x] 4.10 Implementar `marcar_enviando(comunicacion_id) -> None` y `marcar_enviado(comunicacion_id) -> None` y `marcar_error(comunicacion_id, detalle: str) -> None`
- [x] 4.11 Implementar `resetear_colgados(stale_threshold_minutes: int) -> int` → UPDATE a `Pendiente` los que llevan más de N minutos en `Enviando`

## 5. Service

- [x] 5.1 Crear `ComunicacionService` en `backend/app/services/comunicacion_service.py`
- [x] 5.2 Implementar `preview(request, permission_ctx) -> list[ComunicacionPreviewItemSchema]` → renderiza plantilla por alumno con `string.Template`; sin persistencia; valida variables disponibles (422 si variable inválida)
- [x] 5.3 Implementar `encolar_lote(request, materia_id, permission_ctx) -> ComunicacionLoteResponseSchema` → verifica titularidad de asignación si `is_propio`; crea lote; audita `COMUNICACION_ENVIAR`; retorna schema con flag `requiere_aprobacion`
- [x] 5.4 Implementar `get_estado_lote(lote_id, permission_ctx) -> LoteEstadoSchema` → verifica scope (creador o `comunicacion:aprobar`); delega a repository
- [x] 5.5 Implementar `aprobar_lote(lote_id, permission_ctx) -> int` → verifica `comunicacion:aprobar`; delega; audita `COMUNICACION_APROBAR`
- [x] 5.6 Implementar `cancelar_lote(lote_id, permission_ctx) -> int` → verifica scope; delega
- [x] 5.7 Implementar `cancelar_uno(comunicacion_id, permission_ctx) -> None` → verifica scope; delega; valida transición
- [x] 5.8 Implementar `retry_uno(comunicacion_id, permission_ctx) -> None` → verifica scope; delega; valida que sea `Error`

## 6. Router — Endpoints

- [x] 6.1 Crear `backend/app/api/v1/routers/comunicaciones.py` y registrar en `main.py` con prefijo `/api/comunicaciones`
- [x] 6.2 `POST /api/comunicaciones/preview` → guard `comunicacion:enviar`; llama service.preview; retorna lista de `ComunicacionPreviewItemSchema`
- [x] 6.3 `POST /api/comunicaciones/lote` → guard `comunicacion:enviar`; llama service.encolar_lote; retorna `ComunicacionLoteResponseSchema`
- [x] 6.4 `GET /api/comunicaciones/lote/{lote_id}/estado` → guard `comunicacion:enviar`; llama service.get_estado_lote; retorna `LoteEstadoSchema`
- [x] 6.5 `POST /api/comunicaciones/lote/{lote_id}/aprobar` → guard `comunicacion:aprobar`; llama service.aprobar_lote
- [x] 6.6 `POST /api/comunicaciones/lote/{lote_id}/cancelar` → guard `comunicacion:aprobar`; llama service.cancelar_lote
- [x] 6.7 `POST /api/comunicaciones/{comunicacion_id}/cancelar` → guard `comunicacion:enviar`; llama service.cancelar_uno
- [x] 6.8 `POST /api/comunicaciones/{comunicacion_id}/retry` → guard `comunicacion:enviar`; llama service.retry_uno

## 7. Worker de despacho

- [x] 7.1 Crear `backend/app/workers/comunicacion_worker.py` con clase `ComunicacionWorker` y método `run_once(db_session)` → resetea colgados al arranque, toma batch de elegibles, despacha cada uno vía `N8NClient`
- [x] 7.2 Agregar `COMUNICACION_DISPATCH_INTERVAL_SECONDS` (default 30), `COMUNICACION_BATCH_SIZE` (default 50), `COMUNICACION_STALE_THRESHOLD_MINUTES` (default 10) a `core/config.py`
- [x] 7.3 Integrar el nuevo loop `_comunicacion_dispatch_loop` en `workers/main.py` dentro del `asyncio.gather` existente
- [x] 7.4 Verificar que el worker NO toma mensajes si `N8N_WEBHOOK_URL` es None/vacío (log error crítico y skip)

## 8. Tests — Safety net + TDD

- [x] 8.1 Verificar baseline: correr suite existente, capturar `N tests passing`
- [x] 8.2 Test: preview renderiza variables correctamente por alumno
- [x] 8.3 Test: preview con variable inválida → 422
- [x] 8.4 Test: preview no persiste nada (0 filas en `comunicacion` tras el call)
- [x] 8.5 Test: encolado crea N registros con mismo `lote_id` y `destinatario` cifrado (no en claro)
- [x] 8.6 Test: encolado con tenant `requiere_aprobacion=True` → mensajes Pendiente, `requiere_aprobacion=True` en respuesta
- [x] 8.7 Test: usuario sin `comunicacion:enviar` → 403
- [x] 8.8 Test: PROFESOR intenta encolar para asignación ajena → 403
- [x] 8.9 Test: estado de lote agrega correctamente por estado
- [x] 8.10 Test: aprobar lote → todos los Pendiente quedan `aprobado=True`; se audita `COMUNICACION_APROBAR`
- [x] 8.11 Test: cancelar lote → todos los Pendiente pasan a `Cancelado`
- [x] 8.12 Test: cancelar mensaje Enviado → 422 (transición inválida)
- [x] 8.13 Test: retry de mensaje Error → vuelve a Pendiente
- [x] 8.14 Test: retry de mensaje no-Error → 422
- [x] 8.15 Test: máquina de estados — transición inválida rechazada
- [x] 8.16 Test: aislamiento multi-tenant (Tenant B no ve lotes de Tenant A → 404)
- [x] 8.17 Test worker: `run_once` con N8N mock exitoso → mensaje transiciona a Enviado
- [x] 8.18 Test worker: `run_once` con N8N mock fallido → mensaje transiciona a Error con `error_detalle`
- [x] 8.19 Test worker: tenant con `requiere_aprobacion=True` sin `aprobado=True` → worker no despacha
- [x] 8.20 Test worker: `resetear_colgados` transiciona mensajes viejos en Enviando a Pendiente
- [x] 8.21 Test worker: `N8N_WEBHOOK_URL` no configurada → worker no toma mensajes (no hay Enviando)
- [x] 8.22 Test worker: procesa solo `COMUNICACION_BATCH_SIZE` mensajes por ciclo
- [x] 8.23 Test: `destinatario` cifrado en DB (valor almacenado != email original)
- [x] 8.24 Test: `destinatario` descifrado correctamente en el worker antes de enviar a N8N
