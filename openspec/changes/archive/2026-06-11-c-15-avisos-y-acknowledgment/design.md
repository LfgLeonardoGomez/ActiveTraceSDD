# Design: Avisos y Acknowledgment

## Technical Approach

Build the avisos module following C-14 patterns exactly: model + repository + service + router + schemas + migration. The novel domain logic is **audience matching** (RN-20): a SQLAlchemy query that joins the user’s active `Asignacion` records against an `Aviso`’s `alcance` + context fields. Acknowledgment is an idempotent upsert on `(aviso_id, usuario_id)` with `confirmado_at` (RN-19). No denormalized counters — all counts are derived from `AcknowledgmentAviso`.

## Architecture Decisions

| Decision | Options | Trade-offs | Decision |
|----------|---------|-----------|----------|
| Audience query | A) JOIN `Asignacion` in every `mis-avisos` query | Slightly more complex SQL; always correct | **A** — matches user’s roles + context dynamically |
| | B) Precompute audience table | Adds write-time complexity; unnecessary for MVP | |
| rol_destino NULL | A) NULL = "all roles" | Simple, intuitive for global announcements | **A** — explicitly documented |
| | B) NULL = "none" | Would require special-case for global | |
| Ack deduplication | A) Upsert (idempotent) | Clean UX, no 409 on re-ack | **A** — return existing record if already ack’d |
| | B) 409 on duplicate | Confusing UX | |
| Counter strategy | A) Derived counts only | Slower for large N, but always correct | **A** — no denormalized fields |
| | B) Counter columns on Aviso | Risk of drift | |
| cuerpo storage | A) Plain text (MVP) | No rich-text editor needed now | **A** — matches proposal out-of-scope |
| | B) JSON/Markdown | Over-engineering for MVP | |

## Data Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────────┐
│  Router     │────▶│   Service    │────▶│   Repository        │
│ /api/avisos │     │  RN-18/19/20 │     │ tenant-filter + JOIN│
└─────────────┘     └──────────────┘     └─────────────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ record_audit │
                     │ AVISO_PUBLICAR│
                     │ AVISO_CONFIRMAR│
                     └──────────────┘
```

**Audience query (RN-20)**: `Aviso` filtered by `tenant_id`, `activo = true`, `deleted_at IS NULL`, and current time between `inicio_en` and `fin_en`. Then matched against the caller’s `Asignacion` records:

- `Global` → always included
- `PorRol` → included if `rol_destino` IS NULL OR `rol_destino` matches any of the user’s active assignment roles
- `PorMateria` → included if `materia_id` matches any of the user’s active assignments with that `materia_id`
- `PorCohorte` → included if `cohorte_id` matches any of the user’s active assignments with that `cohorte_id`

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `app/models/aviso.py` | Create | `AlcanceAviso`, `SeveridadAviso` StrEnums; `Aviso` model; `AcknowledgmentAviso` model |
| `app/repositories/aviso_repository.py` | Create | CRUD + `list_para_usuario` (audience query) + `acknowledge` (upsert) + `count_acknowledgments` |
| `app/services/aviso_service.py` | Create | Vigency validation, audience match orchestration, ack logic, audit calls |
| `app/schemas/aviso.py` | Create | Pydantic v2 request/response schemas, all `extra='forbid'` |
| `app/api/v1/routers/avisos.py` | Create | 7 endpoints with `require_permission` guards |
| `app/core/audit.py` | Modify | Add `AVISO_PUBLICAR`, `AVISO_CONFIRMAR` to `AuditAction` |
| `app/main.py` | Modify | Register `avisos_router` |
| `alembic/versions/011_aviso_acknowledgment.py` | Create | Schema migration: `aviso` + `acknowledgment_aviso` tables + indexes |

## Interfaces / Contracts

```python
# app/models/aviso.py
class AlcanceAviso(StrEnum):
    GLOBAL = "Global"
    POR_MATERIA = "PorMateria"
    POR_COHORTE = "PorCohorte"
    POR_ROL = "PorRol"

class SeveridadAviso(StrEnum):
    INFO = "Info"
    ADVERTENCIA = "Advertencia"
    CRITICO = "Crítico"

class Aviso(BaseModelMixin, Base):
    __tablename__ = "aviso"
    __table_args__ = (
        Index("ix_aviso_tenant", "tenant_id"),
        Index("ix_aviso_tenant_activo_vigencia", "tenant_id", "activo", "inicio_en", "fin_en"),
        Index("ix_aviso_alcance", "tenant_id", "alcance", "materia_id", "cohorte_id"),
    )

    alcance: Mapped[str] = mapped_column(String(30), nullable=False)
    materia_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("materias.id", ondelete="SET NULL"), nullable=True)
    cohorte_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("cohortes.id", ondelete="SET NULL"), nullable=True)
    rol_destino: Mapped[str | None] = mapped_column(String(30), nullable=True)
    severidad: Mapped[str] = mapped_column(String(30), nullable=False)
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    inicio_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fin_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    requiere_ack: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

class AcknowledgmentAviso(BaseModelMixin, Base):
    __tablename__ = "acknowledgment_aviso"
    __table_args__ = (
        UniqueConstraint("aviso_id", "usuario_id", name="uq_ack_aviso_usuario"),
        Index("ix_ack_aviso_aviso", "aviso_id"),
        Index("ix_ack_aviso_usuario", "usuario_id"),
    )
    aviso_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("aviso.id", ondelete="CASCADE"), nullable=False)
    usuario_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    confirmado_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
```

**Router guards**:
- `POST /api/avisos` → `require_permission("avisos:publicar")`
- `GET /api/avisos` → `require_permission("avisos:publicar")`
- `GET /api/avisos/{id}` → `require_permission("avisos:publicar")`
- `PATCH /api/avisos/{id}` → `require_permission("avisos:publicar")`
- `DELETE /api/avisos/{id}` → `require_permission("avisos:publicar")`
- `GET /api/avisos/mis-avisos` → `require_permission("avisos:confirmar")`
- `POST /api/avisos/{id}/confirmar` → `require_permission("avisos:confirmar")`

## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| Unit | Service vigency validation, audience composition | Parametrized pytest with mocked repository |
| Integration | Repository audience query with real DB | PostgreSQL test container; seed `Asignacion` + `Aviso` + `AcknowledgmentAviso` |
| Integration | Ack upsert idempotency | Run `confirmar` twice; assert same record returned |
| Integration | Router RBAC | 403 when permission missing; 200 when present |
| E2E | Full CRUD + mis-avisos + confirmar flow | Seed data → create aviso → list as publisher → list as user → confirm → verify no longer appears |

**Coverage targets**: ≥90% for RN-18, RN-19, RN-20 paths.

## Migration / Rollout

Migration `011_aviso_acknowledgment.py` creates `aviso` and `acknowledgment_aviso` tables. No data migration needed — new feature. Rollback: drop both tables. No cross-module FK dependencies.

## Open Questions

- [ ] **Acknowledged aviso exclusion**: Should `mis-avisos` exclude ack’d avisos entirely, or show them in a separate "read" section? Proposal says "stop showing" — implement as exclusion.
- [ ] **cuerpo rich text**: Proposal says plain text for MVP. Confirm no Markdown/JSON formatting needed now.
- [ ] **Ordering**: `orden` field exists but no UI sorting requirement defined. Default sort: `orden ASC, created_at DESC`.

(End of document)
