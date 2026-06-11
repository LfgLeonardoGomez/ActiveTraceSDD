# Proposal: Avisos y Acknowledgment

## Intent

Enable COORDINADOR/ADMIN to publish system-wide or scoped announcements (avisos) that target specific audiences by role, materia, or cohorte, with mandatory read confirmation (acknowledgment) and time-boxed visibility — replacing ad-hoc email/WhatsApp broadcasts with traceable, rule-governed communication.

## Scope

### In Scope
- `Aviso` model: alcance (Global/PorMateria/PorCohorte/PorRol), severidad (Info/Advertencia/Crítico), vigencia (inicio_en/fin_en), orden, activo, requiere_ack
- `AcknowledgmentAviso` model: confirmation of read by user; counters derived (no denormalization)
- CRUD aviso endpoints under `avisos:publicar` (COORDINADOR/ADMIN)
- Listing/filtering by scope, vigency window (RN-18), audience match (RN-20)
- Acknowledgment endpoint under `avisos:confirmar` (all roles); ack makes aviso stop showing to that user
- Migration 011: `aviso`, `acknowledgment_aviso`
- Audit action codes: `AVISO_PUBLICAR`, `AVISO_CONFIRMAR`

### Out of Scope
- Push notifications / real-time delivery (future: WebSocket integration)
- Rich-text editor for cuerpo (stored as plain text for MVP)
- Rich media attachments in avisos
- Email dispatch of avisos (separate from comunicaciones worker)

## Capabilities

### New Capabilities
- `avisos-crud`: Creation, update, deactivation, and listing of avisos with scope filters (alcance, materia, cohorte, rol_destino, severidad, vigencia). COORDINADOR/ADMIN manage; all roles read according to scope (RN-18, RN-20, F3.5).
- `avisos-acknowledgment`: Acknowledgment of receipt by any role with `avisos:confirmar`. Derives view/ack counts from AcknowledgmentAviso. Acknowledged avisos stop appearing for that user (RN-19).

### Modified Capabilities
- `audit-action-helper`: Add `AVISO_PUBLICAR` and `AVISO_CONFIRMAR` action codes to the audit helper registry.

## Approach

Follow C-14 (evaluaciones) patterns exactly: model with `BaseModelMixin`, repository with tenant scope, service with business rules (vigency filtering, audience matching), router at `/api/avisos` with `require_permission` guards. The key domain logic is the **audience query**: compose a SQLAlchemy filter that matches a user's roles + materia/cohorte assignments against the aviso's alcance/contexto. Acknowledgment is a simple upsert on `(aviso_id, usuario_id)` with `confirmado_at` timestamp. No denormalized counters — count queries always hit `AcknowledgmentAviso`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/models/aviso.py` | New | Aviso + AcknowledgmentAviso ORM models |
| `app/repositories/aviso_repository.py` | New | Tenant-scoped CRUD + audience query + ack upsert |
| `app/services/aviso_service.py` | New | Vigency, audience match, ack logic (RN-18/19/20) |
| `app/schemas/aviso.py` | New | Pydantic request/response schemas |
| `app/api/v1/routers/avisos.py` | New | REST endpoints `/api/avisos/*` |
| `app/core/audit.py` | Modified | Add AVISO_PUBLICAR, AVISO_CONFIRMAR codes |
| `app/main.py` | Modified | Register avisos router |
| `alembic/versions/011_aviso_acknowledgment.py` | New | Schema migration |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Audience query complexity (4 alcance types × many-to-many roles) | Med | Test all 4 alcance paths; use repository integration tests with real DB |
| Performance on unacknowledged aviso list for large tenants | Low | Index on `(tenant_id, activo, inicio_en, fin_en)`; paginate |
| Edge case: aviso with NULL rol_destino means "all roles" but misread as "nobody" | Med | Explicit RN-20 rule in service test: NULL rol_destino = all authenticated |

## Rollback Plan

Revert migration 011 (DROP TABLES `aviso`, `acknowledgment_aviso`). Remove router registration from main.py. No cross-module FK dependencies — clean rollback.

## Dependencies

- C-06 (estructura-academica): Materia and Cohorte models exist — COMPLETED ✓
- C-04 (rbac-permisos-finos): `avisos:publicar` and `avisos:confirmar` already seeded in migration 002 — COMPLETED ✓
- C-07 (usuarios-y-asignaciones): Usuario and Asignacion models for audience matching — COMPLETED ✓

## Success Criteria

- [ ] COORDINADOR/ADMIN can CRUD avisos with all alcance types and severidad levels
- [ ] Avisos outside vigency window are invisible (RN-18)
- [ ] Users see only avisos matching their roles/cohorte/materia (RN-20)
- [ ] Acknowledgment records a timestamp; acknowledged avisos stop showing for that user (RN-19)
- [ ] View/ack counters derived from AcknowledgmentAviso, zero denormalized fields
- [ ] Integration test coverage ≥90% for business rules RN-18/19/20