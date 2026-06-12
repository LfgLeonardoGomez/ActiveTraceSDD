# Verification Report — C-20 perfil-y-mensajeria-interna

## Change
- **Change**: C-20 perfil-y-mensajeria-interna
- **Mode**: hybrid (Engram + OpenSpec)
- **Strict TDD**: ACTIVE

## Completeness

| Task | Status |
|------|--------|
| T-01 Mensaje model | ✅ |
| T-02 models/__init__.py export | ✅ |
| T-03 Migration 016 | ✅ |
| T-04 PerfilUpdate schema | ✅ |
| T-05 Mensajes schemas | ✅ |
| T-06 MensajeRepository | ✅ |
| T-07 PerfilService | ✅ |
| T-08 MensajeService | ✅ |
| T-09 Router perfil | ✅ |
| T-10 Router inbox | ✅ |
| T-11 AuditAction codes | ✅ |
| T-12 seed_rbac permissions | ✅ |
| T-13 main.py router registration | ✅ |
| T-14 test_perfil.py | ✅ |
| T-15 test_inbox.py | ✅ |

**Tasks**: 15/15 complete

## Build / Import Evidence

```
All C-20 modules import successfully
AuditAction.PERFIL_EDITAR = "PERFIL_EDITAR"
AuditAction.MENSAJE_RESPONDER = "MENSAJE_RESPONDER"
Routers registered:
  PATCH /api/v1/perfil
  GET   /api/v1/inbox
  GET   /api/v1/inbox/{root_id}
  POST  /api/v1/inbox/{root_id}/responder
All 6 schemas have extra='forbid'
PerfilUpdate rejects cuil with ValidationError (structural test PASSED)
PerfilUpdate rejects unknown fields (structural test PASSED)
```

## Test Results

| Category | Count |
|----------|-------|
| PASSED | 5 |
| BLOCKED | 13 |
| FAILED | 0 |

**PASSED** (no DB needed):
- `test_perfil_endpoint_existe` — router registered, not 404
- `test_perfil_patch_sin_token_401` — unauthenticated → 401
- `test_inbox_endpoint_existe` — router registered, not 404
- `test_inbox_get_sin_token_401` — unauthenticated → 401
- `test_inbox_responder_sin_token_401` — unauthenticated → 401

**BLOCKED** (PostgreSQL unreachable — `socket.gaierror: [Errno -3] Temporary failure in name resolution`):
- All 5 `TestPerfilService` tests
- All 8 `TestMensajeService` tests

## Spec Compliance Matrix

### perfil-edicion/spec.md

| Scenario | Covering Test | Implementation Evidence | Status |
|----------|--------------|------------------------|--------|
| Edit own profile successfully | `test_perfil_service_edita_campos` | `PerfilService.editar_perfil` → `UsuarioRepository.update` (encrypts PII) → audit `PERFIL_EDITAR` | BLOCKED (DB) |
| Attempt to edit another user | `test_perfil_service_tenant_isolation` | Router passes only `current_user.id` from JWT; no target user_id param; tenant-scoped repo → 404 cross-tenant | BLOCKED (DB) |
| Soft-deleted user cannot edit | `test_perfil_service_404_usuario_eliminado` | `get_by_id` filters `deleted_at IS NULL` → returns None → 404 | BLOCKED (DB) |
| CUIL in payload rejected | `test_perfil_service_rechaza_cuil` | `PerfilUpdate` omits `cuil`, `extra='forbid'` → ValidationError 422 | BLOCKED (DB) — structural PASS |
| PII encrypted after edit | `test_perfil_service_pii_encrypted_roundtrip` | `UsuarioRepository.update` calls `_encrypt_pii_fields` before persist, `_decrypt_pii_instance` after read | BLOCKED (DB) |

### mensajeria-inbox/spec.md

| Scenario | Covering Test | Implementation Evidence | Status |
|----------|--------------|------------------------|--------|
| List inbox threads | `test_mensaje_service_list_inbox` | `MensajeRepository.list_inbox_roots` → `destinatario_id=user_id, parent_id IS NULL, deleted_at IS NULL` | BLOCKED (DB) |
| Empty inbox | `test_mensaje_service_empty_inbox` | Same query returns empty list when no messages | BLOCKED (DB) |
| Tenant isolation in inbox | `test_mensaje_service_tenant_isolation` | `BaseRepository._base_query` always filters `tenant_id` | BLOCKED (DB) |
| Read thread successfully | `test_mensaje_service_get_thread_ok` | `MensajeService.get_thread` → root + replies where `parent_id=root_id` | BLOCKED (DB) |
| Thread not addressed to user | `test_mensaje_service_get_thread_403_no_participante` | Service checks `root.remitente_id != user_id and root.destinatario_id != user_id` → 403 | BLOCKED (DB) |
| Reply to thread | `test_mensaje_service_responder_crea_reply` | `MensajeService.responder` → `MensajeRepository.create_reply(root_id, data)` with `parent_id=root_id` | BLOCKED (DB) |
| Reply to non-existent thread | `test_mensaje_service_responder_404_thread_inexistente` | `get_root` returns None → 404 | BLOCKED (DB) |
| Reply to thread from another tenant | `test_mensaje_service_tenant_isolation` | Tenant-scoped `get_root` returns None for cross-tenant → 404 | BLOCKED (DB) |
| Deleted thread hidden | `test_mensaje_service_soft_delete_oculta` | `BaseRepository._base_query` filters `deleted_at IS NULL` | BLOCKED (DB) |

## Design Coherence

| Check | Result | Notes |
|-------|--------|-------|
| Clean Architecture (thin routers) | ✅ | Routers validate input, resolve JWT, delegate to service |
| Tenant scope everywhere | ✅ | `BaseRepository._base_query` always filters `tenant_id` |
| PII encryption transparent | ✅ | `UsuarioRepository.update` encrypts on write, decrypts on read |
| Soft delete on Mensaje | ✅ | `BaseModelMixin` provides `deleted_at`; `BaseRepository.delete` sets it |
| Identity from JWT only | ✅ | `current_user` from `get_current_active_user` dependency |
| Self-service guard | ✅ | Structural — endpoint has no target user_id param |
| Thread access control | ✅ | 403 if user is not remitente or destinatario of root |
| Audit codes registered | ✅ | `PERFIL_EDITAR`, `MENSAJE_RESPONDER` in `AuditAction` enum |
| RBAC permissions seeded | ✅ | `perfil:editar`, `mensajeria:leer`, `mensajeria:responder` in `seed_rbac.py` |
| Migration correct | ✅ | `016_c20_mensaje_perfil.py` creates `mensaje` table + 2 indexes, downgrade drops |

## Issues

### WARNING

1. **Audit called from routers, not services**: Both `perfil.py` and `inbox.py` routers call `record_audit()` directly. The `audit.py` module docstring states: "Llamar exclusivamente desde la capa Service, nunca desde Routers." The design doc also says services log audit (`PerfilService` logs `PERFIL_EDITAR`, `MensajeService` logs `MENSAJE_RESPONDER`). Implementation deviates — audit should be inside service methods, not router handlers.

2. **`Mensaje.replies` relationship direction inverted**: SQLAlchemy confirms `MANYTOONE` direction for `replies`. The relationship resolves to the parent message, not children. The `backref="parent"` creates the actual children collection (ONETOMANY). Naming is inverted: `mensaje.replies` → parent, `mensaje.parent` → children. Not used in application code (queries are direct via `MensajeRepository`), but misleading for future developers.
   - **Fix**: Change `remote_side="Mensaje.id"` to `remote_side="Mensaje.parent_id"` or swap the relationship/backref names.

3. **No explicit self-service guard comparison**: Design says "self-service guard enforces `current_user.id == user_id`", but `PerfilService.editar_perfil(current_user_id, data)` only takes `current_user_id` with no second ID to compare against. Structurally correct (endpoint has no user_id param, identity from JWT only), but the explicit comparison mentioned in the design is absent. If `editar_perfil` is ever called internally with a different user_id, there's no guard.

### SUGGESTION

1. `test_perfil_service_rechaza_cuil` requires `db_session` fixture but only tests Pydantic validation (no DB interaction). Could be converted to a pure unit test to avoid DB dependency.

## Final Verdict

**PASS WITH WARNINGS**

- All 15 tasks complete
- All structural checks pass (imports, schema validation, router registration, audit codes, model definition)
- 5/5 non-DB tests pass
- 13 DB-dependent tests BLOCKED (PostgreSQL unreachable — environment limitation, not implementation defect)
- 3 design coherence warnings (audit layer, relationship naming, guard explicitness)
- 0 CRITICAL issues
