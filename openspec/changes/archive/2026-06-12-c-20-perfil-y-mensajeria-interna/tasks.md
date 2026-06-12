# Tasks: Profile & Internal Messaging (C-20)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~620 (code ~380 + tests ~240) |
| 400-line budget risk | High |
| 800-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR (within 800-line budget) |
| Delivery strategy | single-pr |
| Chain strategy | N/A |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: N/A
400-line budget risk: High

## Phase 1: Foundation (Migration + Model)

- [x] **T-01** Create `backend/app/models/mensaje.py` — `Mensaje` model with `BaseModelMixin`, columns: `remitente_id` FK(usuarios.id), `destinatario_id` FK(usuarios.id), `asunto` String(500), `cuerpo` Text, `parent_id` FK(mensaje.id) nullable self-ref. Add relationship `replies` (remote_side=self.id).
- [x] **T-02** Register model in `backend/app/models/__init__.py` — add `from app.models.mensaje import Mensaje` and append to `__all__`.
- [x] **T-03** Create migration `backend/alembic/versions/016_c20_mensaje_perfil.py` — `down_revision = "015_c18_liquidaciones"`. Creates `mensaje` table with indexes: `(tenant_id, destinatario_id, parent_id, deleted_at)` and `(tenant_id, parent_id, created_at)`. Downgrade drops table.

## Phase 2: Schemas (Pydantic DTOs)

- [x] **T-04** Create `backend/app/schemas/perfil.py` — `PerfilUpdate` with `extra='forbid'`: `nombre`, `apellidos`, `email`, `dni`, `cbu`, `alias_cbu`, `banco`, `regional`, `legajo_profesional`, `facturador` (all Optional). `cuil` MUST be absent.
- [x] **T-05** Create `backend/app/schemas/mensajes.py` — `MensajeRead` (id, remitente_id, asunto, cuerpo, created_at), `InboxThreadRead` (same shape for root listing), `InboxThreadDetailRead` (root + `replies: list[MensajeRead]`), `MensajeReplyCreate` (asunto Optional, cuerpo required). All with `extra='forbid'`, `from_attributes=True` where applicable.

## Phase 3: Repository

- [x] **T-06** Create `backend/app/repositories/mensaje_repository.py` — `MensajeRepository(BaseRepository[Mensaje])`. Methods: `list_inbox_roots(user_id)` → roots where `destinatario_id=user_id`, `parent_id IS NULL`, `deleted_at IS NULL`, ordered by latest reply `created_at DESC`. `get_thread(root_id)` → root + replies where `parent_id=root_id`, `deleted_at IS NULL`, ordered `created_at ASC`. `get_root(root_id)` → single root by ID with tenant scope. `create_reply(root_id, data)` → create with `parent_id=root_id`.

## Phase 4: Services

- [x] **T-07** Create `backend/app/services/perfil_service.py` — `PerfilService(db_session, tenant_id)`. Method `editar_perfil(current_user_id, data: dict)` — self-service guard: resolves user via `UsuarioRepository.get_by_id(current_user_id)`, returns 404 if None/deleted. Delegates to `UsuarioRepository.update(current_user_id, data)`. Returns updated `Usuario`.
- [x] **T-08** Create `backend/app/services/mensaje_service.py` — `MensajeService(db_session, tenant_id)`. Methods: `list_inbox(user_id)` → delegates to `MensajeRepository.list_inbox_roots`. `get_thread(root_id, user_id)` → fetches root, verifies user is `remitente_id` or `destinatario_id` (403 if not), returns root + replies. `responder(root_id, user_id, data)` → access check, creates reply via repo, returns `Mensaje`.

## Phase 5: Routers

- [x] **T-09** Create `backend/app/api/v1/routers/perfil.py` — `PATCH /api/v1/perfil`, guard `require_permission("perfil:editar")`. Thin router: resolves `current_user` from JWT, calls `PerfilService.editar_perfil(current_user.id, body.model_dump(exclude_unset=True))`. Returns `UsuarioDetailRead` (200). Calls `record_audit(PERFIL_EDITAR)` after success.
- [x] **T-10** Create `backend/app/api/v1/routers/inbox.py` — Three endpoints: `GET /api/v1/inbox` (guard `mensajeria:leer`) → `list[InboxThreadRead]`. `GET /api/v1/inbox/{id}` (guard `mensajeria:leer`) → `InboxThreadDetailRead`. `POST /api/v1/inbox/{id}/responder` (guard `mensajeria:responder`) → `MensajeRead` (201). All resolve identity from JWT. Reply endpoint calls `record_audit(MENSAJE_RESPONDER)`.

## Phase 6: Wiring

- [x] **T-11** Modify `backend/app/core/audit.py` — add `PERFIL_EDITAR = "PERFIL_EDITAR"` and `MENSAJE_RESPONDER = "MENSAJE_RESPONDER"` to `AuditAction` enum.
- [x] **T-12** Modify `backend/app/core/seed_rbac.py` — add permission catalog entries: `perfil:editar`, `mensajeria:leer`, `mensajeria:responder` (all granted to all authenticated roles).
- [x] **T-13** Modify `backend/app/main.py` — import and `app.include_router()` for `perfil_router` and `inbox_router`.

## Phase 7: Testing

- [x] **T-14** Create `backend/tests/test_perfil.py` — Unit tests for `PerfilService`: self-service guard (403 on mismatch is N/A since ID comes from JWT, test 404 on soft-deleted user). Integration tests: `PATCH /api/v1/perfil` updates fields, rejects `cuil` with 422, PII encrypted at rest, audit `PERFIL_EDITAR` logged, tenant isolation.
- [x] **T-15** Create `backend/tests/test_inbox.py` — Unit tests for `MensajeService`: thread access (403 if not recipient/sender), soft-delete filtering. Integration tests: `GET /api/v1/inbox` lists roots, tenant isolation (404 cross-tenant), `GET /api/v1/inbox/{id}` returns root + replies, `POST /api/v1/inbox/{id}/responder` creates reply with `parent_id`, 404 on nonexistent thread, audit `MENSAJE_RESPONDER` logged.

## Implementation Order

Phase 1 → 2 → 3 → 4 → 5 → 6 → 7 (strict dependency chain). Each phase depends on the previous. Within each phase, tasks are independent and can be done in any order.
