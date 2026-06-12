# Design: Profile & Internal Messaging (C-20)

## Technical Approach

Profile editing and inbox messaging are delivered as two self-service endpoints under the existing Clean Architecture stack. Profile editing reuses `UsuarioService` and `UsuarioRepository` (C-07) with a self-service guard that enforces `current_user.id == target_user.id`. CUIL read-only is enforced at the schema level (`cuil` omitted from `PerfilUpdate` + `extra='forbid'`). Inbox introduces a single `Mensaje` table with a `parent_id` self-referencing FK for thread threading. All layers follow the established patterns: thin routers, business logic in services, tenant-scoped repositories, and soft-delete by default.

## Architecture Decisions

| Decision | Option | Tradeoff | Choice |
|----------|--------|----------|--------|
| Self-service guard location | Router vs Service | Router bypass risk if service is called internally | **Service** — `PerfilService` enforces `current_user.id == user_id` before delegating to `UsuarioRepository` |
| CUIL read-only enforcement | Schema omission vs DB constraint | Schema omission is simpler and fail-fast; DB constraint is redundant with schema | **Schema omission** — `PerfilUpdate` omits `cuil`; `extra='forbid'` rejects any payload containing it with 422 |
| Thread model | Single table self-FK vs separate thread+message tables | Self-FK is simpler and sufficient for 1-level replies; separate tables add complexity | **Single `Mensaje` table** with `parent_id` self-FK. Root = `parent_id IS NULL`, replies point to root |
| Thread access control | Recipient-only vs Recipient-or-Sender | Recipient-only hides sent messages from inbox; sender needs to read replies | **Recipient-or-Sender** for `GET /inbox/{id}` and `POST /inbox/{id}/responder`; `GET /inbox` lists only roots where user is recipient |
| PII handling on profile edit | Reuse C-07 repository vs new service logic | Reuse guarantees consistency; new logic risks divergence | **Reuse** — `PerfilService` calls `UsuarioRepository.update`, which transparently re-encrypts AES-256 PII and recalculates `email_hash` |

## Data Flow

```
Profile Edit:
  JWT → Router → PerfilService(self-guard) → UsuarioRepository(encrypt) → DB
                                    ↓
                              Audit(PERFIL_EDITAR)

Inbox Reply:
  JWT → Router → MensajeService(access-check) → MensajeRepository → DB
                                    ↓
                              Audit(MENSAJE_RESPONDER)
```

## Data Model Changes

- **New model**: `Mensaje` (`app/models/mensaje.py`)
  - `id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at` — from `BaseModelMixin`
  - `remitente_id`: `FK(usuarios.id)`, non-nullable
  - `destinatario_id`: `FK(usuarios.id)`, non-nullable
  - `asunto`: `String(500)`, non-nullable
  - `cuerpo`: `Text`, non-nullable
  - `parent_id`: `FK(mensaje.id)`, nullable — self-referencing FK for thread threading
- **Migration**: `backend/alembic/versions/016_c20_mensaje_perfil.py` (next available after `015_c18_liquidaciones.py`). Single migration creates `mensaje` table + indexes.
- **No changes** to `Usuario` model — all editable fields already exist (C-07).

## API Design

| Method | Path | Guard | Request | Response |
|--------|------|-------|---------|----------|
| `PATCH` | `/api/v1/perfil` | `perfil:editar` | `PerfilUpdate` | `UsuarioDetailRead` |
| `GET` | `/api/v1/inbox` | `mensajeria:leer` | — | `list[InboxThreadRead]` |
| `GET` | `/api/v1/inbox/{id}` | `mensajeria:leer` | — | `InboxThreadDetailRead` |
| `POST` | `/api/v1/inbox/{id}/responder` | `mensajeria:responder` | `MensajeReplyCreate` | `MensajeRead` (201) |

### Schemas

- `PerfilUpdate` (Pydantic, `extra='forbid'`): `nombre`, `apellidos`, `email`, `dni`, `cbu`, `alias_cbu`, `banco`, `regional`, `legajo_profesional`, `facturador` — all optional. `cuil` is **absent**.
- `InboxThreadRead`: `id`, `remitente_id`, `asunto`, `cuerpo`, `created_at`
- `InboxThreadDetailRead`: root `InboxThreadRead` + `replies: list[MensajeRead]` ordered by `created_at ASC`
- `MensajeReplyCreate`: `asunto` (optional, defaults to `"Re: {root.asunto}"`), `cuerpo` (required)
- `MensajeRead`: `id`, `remitente_id`, `asunto`, `cuerpo`, `created_at`

## Layer Responsibilities

- **Router**: thin — validates input, resolves `current_user` from JWT, delegates to service. No business logic. No DB access.
- **Service**:
  - `PerfilService`: enforces self-service guard (`current_user.id == user_id` → 403 if mismatch), delegates to `UsuarioRepository.update`, logs `PERFIL_EDITAR` audit.
  - `MensajeService`: enforces thread access (user must be recipient or sender of root → 403 if not), creates replies with `parent_id = root.id`, logs `MENSAJE_RESPONDER` audit.
- **Repository**:
  - `UsuarioRepository` (existing): transparent AES-256 encryption/decryption on update/read.
  - `MensajeRepository` (new): tenant-scoped queries. `list_inbox_roots(user_id)` filters by `destinatario_id`, `parent_id IS NULL`, `deleted_at IS NULL`. `get_thread(root_id)` returns root + replies where `parent_id = root_id` and `deleted_at IS NULL`.
- **Model**: `Mensaje` ORM definition with `BaseModelMixin` (soft delete, timestamps, tenant_id).

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/models/mensaje.py` | Create | `Mensaje` model with `parent_id` self-FK |
| `backend/app/schemas/perfil.py` | Create | `PerfilUpdate` (omits `cuil`, `extra='forbid'`) |
| `backend/app/schemas/mensajes.py` | Create | `InboxThreadRead`, `InboxThreadDetailRead`, `MensajeReplyCreate`, `MensajeRead` |
| `backend/app/repositories/mensaje_repository.py` | Create | Tenant-scoped thread queries + soft delete filter |
| `backend/app/services/perfil_service.py` | Create | Self-service guard + delegation to `UsuarioRepository` |
| `backend/app/services/mensaje_service.py` | Create | Thread access control + reply creation |
| `backend/app/api/v1/routers/perfil.py` | Create | `PATCH /api/v1/perfil` |
| `backend/app/api/v1/routers/inbox.py` | Create | `GET /inbox`, `GET /inbox/{id}`, `POST /inbox/{id}/responder` |
| `backend/alembic/versions/016_c20_mensaje_perfil.py` | Create | Single migration: `mensaje` table + indexes |
| `backend/app/core/audit.py` | Modify | Add `PERFIL_EDITAR`, `MENSAJE_RESPONDER` to `AuditAction` |
| `backend/app/core/seed_rbac.py` | Modify | Add `perfil:editar`, `mensajeria:leer`, `mensajeria:responder` to seed catalog |
| `backend/app/models/__init__.py` | Modify | Export `Mensaje` |
| `backend/app/main.py` | Modify | `app.include_router(perfil_router)` and `app.include_router(inbox_router)` |

## Permissions

New permission codes seeded via `seed_rbac.py` (all granted to all authenticated roles by default):

- `perfil:editar` — self-service profile edit
- `mensajeria:leer` — list inbox and read threads
- `mensajeria:responder` — reply in existing threads

## Audit

New `AuditAction` codes in `backend/app/core/audit.py`:

- `PERFIL_EDITAR` — logged on every successful `PATCH /api/v1/perfil`
- `MENSAJE_RESPONDER` — logged on every successful `POST /api/v1/inbox/{id}/responder`

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `PerfilService` self-service guard (403 on mismatch), `MensajeService` thread access (403 if not recipient/sender), soft delete filtering | pytest with real `db_session` fixture (no mocks) |
| Integration | `PATCH /perfil` updates editable fields and rejects `cuil` with 422, `GET /inbox` tenant isolation, `POST /inbox/{id}/responder` creates reply linked to root | `httpx.AsyncClient` against FastAPI app with `async_client` fixture |
| E2E | Full flow: user edits profile → sees updated PII decrypted → receives message → reads thread → replies → audit entries present | Reuse existing `default_tenant` fixture + create users/messages inline |

## Migration / Rollout

- **Schema migration**: single Alembic revision `016_c20_mensaje_perfil.py` creates `mensaje` table, indexes on `(tenant_id, destinatario_id, parent_id, deleted_at)` and `(tenant_id, parent_id, created_at)`.
- **Rollback**: `alembic downgrade` drops `mensaje` table. No impact on existing `usuarios` data.
- **No data migration** required.

## Open Questions

- None.
