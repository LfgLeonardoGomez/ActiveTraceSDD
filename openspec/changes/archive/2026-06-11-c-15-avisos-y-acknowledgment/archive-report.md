# Archive Report: C-15 Avisos y Acknowledgment

**Archived on**: 2026-06-11  
**Previous path**: `openspec/changes/c-15-avisos-y-acknowledgment/`  
**Archive path**: `openspec/changes/archive/2026-06-11-c-15-avisos-y-acknowledgment/`

## Intent

Enable COORDINADOR/ADMIN to publish system-wide or scoped announcements (avisos) targeting specific audiences by role, materia, or cohorte, with mandatory read confirmation (acknowledgment) and time-boxed visibility.

## Scope

- **In scope**: Aviso model (alcance, severidad, vigencia), AcknowledgmentAviso model, CRUD endpoints under `avisos:publicar`, listing/filtering by scope/vigency/audience, acknowledgment endpoint under `avisos:confirmar`, Migration 011, audit codes.
- **Out of scope**: Push notifications, rich-text editor, file attachments, email dispatch.

## Implementation Summary

| Area | Status | Files |
|------|--------|-------|
| Models | ✅ Created | `app/models/aviso.py` |
| Migration | ✅ Created | `alembic/versions/011_aviso_acknowledgment.py` |
| Schemas | ✅ Created | `app/schemas/aviso.py` |
| Repository | ✅ Created | `app/repositories/aviso_repository.py` |
| Service | ✅ Created | `app/services/aviso_service.py` |
| Router | ✅ Created | `app/api/v1/routers/avisos.py` |
| Audit codes | ✅ Added | `AVISO_CREAR`, `AVISO_ACTUALIZAR`, `AVISO_ELIMINAR`, `AVISO_CONFIRMAR` |
| Wiring | ✅ Done | Router registered in `app/main.py`, models in `__init__.py` |
| RBAC seeding | ✅ Pre-existing | C-04 already seeded `avisos:publicar` and `avisos:confirmar` (migration 002) |
| Testing | ⏭️ Skipped | Testing tasks (Phase 7) skipped per user request |

## Specs Synced to Main

Both domains were **new** — no existing main spec to merge. Copied delta specs directly.

| Domain | Action | Spec Path |
|--------|--------|-----------|
| `avisos-crud` | Created | `openspec/specs/avisos-crud/spec.md` |
| `avisos-acknowledgment` | Created | `openspec/specs/avisos-acknowledgment/spec.md` |

## Archive Contents

- `proposal.md` ✅
- `specs/avisos-crud/spec.md` ✅
- `specs/avisos-acknowledgment/spec.md` ✅
- `specs/audit-action-helper/spec.md` ✅
- `design.md` ✅
- `tasks.md` ✅

## Task Reconciliation Note

Phase 7 testing tasks (7.1–7.5) remain unchecked (`- [ ]`) in `tasks.md`. These were **testing-only tasks** skipped by user request. The user/orchestrator explicitly instructed to proceed with archive despite these unchecked items. Implementation tasks (Phases 1–6) are all complete. This archive is marked as **intentional-with-warnings** for the skipped testing tasks.

## Source of Truth Updated

The following main specs now reflect the new behavior:
- `openspec/specs/avisos-crud/spec.md`
- `openspec/specs/avisos-acknowledgment/spec.md`

## Dependencies

- C-06 (estructura-academica): Materia and Cohorte models — COMPLETED
- C-04 (rbac-permisos-finos): `avisos:publicar` and `avisos:confirmar` seeded — COMPLETED
- C-07 (usuarios-y-asignaciones): Usuario and Asignacion models — COMPLETED

## SDD Cycle Complete

The change has been fully planned, implemented (Phases 1-6), and archived. Testing was deferred per user instruction.
