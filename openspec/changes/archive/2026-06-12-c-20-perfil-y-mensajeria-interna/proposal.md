# Proposal: Profile & Internal Messaging (C-20)

## Intent

Users need to edit their own profile data (banking, fiscal, regional, payment method) and communicate with other registered users through an internal inbox — independently from the outbound email system (C-12). CUIL must be read-only. Logout already exists (C-03).

This change delivers three features from Épica 11: F11.1 (edit profile), F11.2/F3.4 (internal messaging), and F11.3 (explicit logout — already implemented).

## Scope

### In Scope
- `PATCH /api/v1/perfil` — self-service profile editing (name, fiscal/banking data, regional, payment method, professional registration number). CUIL read-only enforced.
- `GET /api/v1/inbox` — list message threads for the authenticated user, scoped by tenant.
- `GET /api/v1/inbox/{id}` — read a message thread with its replies.
- `POST /api/v1/inbox/{id}/responder` — reply within an existing thread.
- New `Mensaje` model with `parent_id` threading (tree-structured replies) and soft delete.
- Pydantic schemas with `extra='forbid'`, AES-256 encryption for PII fields on read/write.
- Audit entries for profile edits (`PERFIL_EDITAR`) and message actions (`MENSAJE_RESPONDER`).
- Alembic migration for `mensaje` table.
- Tests: profile edit (editable vs read-only fields), inbox CRUD, tenant isolation, thread threading.

### Out of Scope
- New message composition (starting a thread) — system-generated messages or future C-20 extension.
- File attachments on messages.
- Real-time/WebSocket notifications for new messages.
- Frontend UI (belongs to C-21/C-23).
- Email notification on new inbox message.
- Message search/full-text indexing.

## Capabilities

### New Capabilities
- `profile-edit`: Self-service profile editing with CUIL read-only enforcement, AES-256 PII handling, and audit logging.
- `inbox-messaging`: Internal message threads between registered users with tree-structured replies, tenant-scoped inbox, and soft delete.

### Modified Capabilities
- `gestion-usuarios`: Profile edit endpoint adds a self-service path parallel to admin CRUD. Existing admin endpoints unchanged; this is additive.

## Approach

**Profile edit**: A new `PATCH /api/v1/perfil` endpoint resolves the current user exclusively from the JWT session (identity rule). A `PerfilUpdate` schema (Pydantic, `extra='forbid'`) whitelists editable fields and omits `cuil` entirely. The `UsuarioService.actualizar_usuario` is reused but wrapped with a self-service guard that enforces `user_id == current_user.id`. CUIL read-only is enforced at schema level (field absent from update DTO) — no CUIL in payload means no mutation. PII fields (email, dni, cbu, alias_cbu) are encrypted/decrypted transparently via `UsuarioRepository` like C-07.

**Inbox messaging**: A single `Mensaje` table with `parent_id` self-referencing FK for thread threading. Each message belongs to a tenant, has a sender, a recipient, subject, body, and timestamps. A thread is a root message (`parent_id IS NULL`) with its descendant replies. The inbox endpoint returns root messages where the user is the recipient, ordered by most recent reply. Reading a thread returns the root + all replies (ordered by `created_at`). Replying creates a new `Mensaje` with `parent_id` pointing to the root message. Soft delete via `deleted_at` on `Mensaje`.

New permissions: `perfil:editar` (self-service, all authenticated users), `mensajeria:leer` and `mensajeria:responder` (all authenticated users).

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/` | New | `mensaje.py` — Mensaje model with parent_id threading |
| `backend/app/schemas/` | New | `perfil.py`, `mensajes.py` — Pydantic DTOs |
| `backend/app/repositories/` | New | `mensaje_repository.py` — tenant-scoped queries |
| `backend/app/services/` | New | `perfil_service.py`, `mensaje_service.py` |
| `backend/app/api/v1/routers/` | New | `perfil.py`, `inbox.py` |
| `backend/app/core/permissions.py` | Modified | Add `perfil:editar`, `mensajeria:leer`, `mensajeria:responder` |
| `backend/app/core/audit.py` | Modified | Add `PERFIL_EDITAR`, `MENSAJE_RESPONDER` audit codes |
| `backend/alembic/versions/` | New | Migration for `mensaje` table |
| `backend/app/schemas/auth.py` | Existing | Logout endpoint already in C-03 — no changes needed |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Thread query performance degrades with deep trees | Low | `parent_id` on root message + index; queries always start from root, not recursive CTE |
| PII exposure in profile edit response | Med | Reuse C-07 encryption/decryption pattern; response DTO returns decrypted PII only to the owner |
| Naming collision with Comunicacion model (C-12 email system) | Low | Separate model (`Mensaje`), separate endpoints (`/inbox` vs `/comunicaciones`), distinct domain |
| Users editing other users' profiles via the self-service endpoint | Med | Enforce `current_user.id == user_id` at service level; fail-closed 403 if mismatch |

## Rollback Plan

1. Remove migration: `alembic downgrade` to drop `mensaje` table.
2. Remove new routers from API router includes.
3. Remove new repositories, services, schemas, models.
4. Permissions and audit codes can remain (harmless) or be removed from seed.
5. No data loss for existing Usuario records — profile edit is additive.

## Dependencies

- C-07 (done ✓): Usuario model with PII encryption, Asignacion model, UsuarioRepository, UsuarioService.
- C-03 (done ✓): Logout endpoint (`POST /api/auth/logout`).
- C-04 (done ✓): RBAC system, permission guard, audit helper.

## Success Criteria

- [ ] `PATCH /api/v1/perfil` updates editable fields and rejects CUIL changes with 422.
- [ ] Profile response returns decrypted PII only to the owning user.
- [ ] `GET /api/v1/inbox` returns threads scoped to the authenticated user's tenant.
- [ ] `POST /api/v1/inbox/{id}/responder` creates a reply linked to the root thread.
- [ ] A user cannot read or reply to threads from another tenant.
- [ ] Audit log records `PERFIL_EDITAR` and `MENSAJE_RESPONDER` actions.
- [ ] Logout (`POST /api/auth/logout`) works without any changes.
- [ ] Test coverage ≥80% lines, ≥90% business rules.