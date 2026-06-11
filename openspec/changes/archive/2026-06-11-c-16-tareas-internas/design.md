# Design: C-16 — Tareas Internas

## Technical Approach

Extend the backend with a complete task-workflow module (`Tarea` + `ComentarioTarea`) reconciling E12 and FL-05. The service layer owns a strict state machine and approval/return flow. All listings are indexed and paginated for high concurrency. The pattern mirrors C-15 (`Aviso`) for consistency.

## Architecture Decisions

| Decision | Options | Trade-off | Choice |
|---|---|---|---|
| E12 reconciliation | Strict E12 vs E12+FL-05 | Strict E12 misses criterio_cierre and approval flow | E12 + FL-05 (additive fields) |
| 5th state vs flag | `EstadoTarea.Devuelta` vs `aprobada: bool` | 5th state complicates queries; flag keeps 4-state enum intact | `aprobada` boolean + `devuelta` flag |
| `contexto_id` | FK validation vs opaque UUID | FK loses polymorphism; opaque matches design intent | Opaque UUID, no FK |
| Comentario soft delete | BaseModelMixin vs hard delete | Pattern consistency; audit trail | BaseModelMixin (soft delete) |

## Data Flow

```
Coordinator → POST /tareas (create + criteria)
  → TareaService.create() → TareaRepository.create()
  → record_audit(TAREA_CREAR)

Docente → GET /tareas/mis-tareas
  → TareaRepository.list_por_asignado()

Docente → PATCH /tareas/{id}/estado (En progreso → Resuelta)
  → TareaService.cambiar_estado() (state machine guard)
  → record_audit(TAREA_ESTADO_CAMBIAR)

Coordinator → POST /tareas/{id}/aprobar or /devolver
  → TareaService.aprobar() / devolver()
  → record_audit(TAREA_APROBAR / TAREA_DEVOLVER)

Any → POST /tareas/{id}/comentarios
  → ComentarioTareaRepository.create()
  → record_audit(TAREA_COMENTAR)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/models/tarea.py` | Create | `Tarea`, `ComentarioTarea`, `EstadoTarea` |
| `backend/app/schemas/tarea.py` | Create | Pydantic schemas with `extra='forbid'` |
| `backend/app/repositories/tarea_repository.py` | Create | CRUD + filters (tenant, asignado, estado, materia) |
| `backend/app/services/tarea_service.py` | Create | State machine, delegation, approval, audit |
| `backend/app/api/v1/routers/tareas.py` | Create | REST endpoints under `/api/tareas/*` |
| `backend/app/core/audit.py` | Modify | Add `TAREA_*` action types |
| `backend/app/models/__init__.py` | Modify | Export `Tarea`, `ComentarioTarea`, `EstadoTarea` |
| `backend/app/main.py` | Modify | Register `tareas_router` |
| `backend/alembic/versions/013_tareas_internas.py` | Create | Schema + indexes migration |

## Data Model

```python
class EstadoTarea(StrEnum):
    PENDIENTE = "Pendiente"
    EN_PROGRESO = "En progreso"
    RESUELTA = "Resuelta"
    CANCELADA = "Cancelada"

class Tarea(BaseModelMixin, Base):
    __tablename__ = "tarea"
    __table_args__ = (
        Index("ix_tarea_tenant_estado", "tenant_id", "estado"),
        Index("ix_tarea_asignado_estado", "tenant_id", "asignado_a", "estado"),
        Index("ix_tarea_materia", "tenant_id", "materia_id"),
    )

    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    criterio_cierre: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default=EstadoTarea.PENDIENTE)
    aprobada: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    devuelta: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    asignado_a: Mapped[UUID] = mapped_column(PG_UUID, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    asignado_por: Mapped[UUID] = mapped_column(PG_UUID, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    revisada_por: Mapped[UUID | None] = mapped_column(PG_UUID, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    revisada_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    materia_id: Mapped[UUID | None] = mapped_column(PG_UUID, ForeignKey("materias.id", ondelete="SET NULL"), nullable=True)
    contexto_id: Mapped[UUID | None] = mapped_column(PG_UUID, nullable=True)  # opaque, no FK

class ComentarioTarea(BaseModelMixin, Base):
    __tablename__ = "comentario_tarea"
    __table_args__ = (
        Index("ix_comentario_tarea_tarea", "tarea_id"),
    )

    tarea_id: Mapped[UUID] = mapped_column(PG_UUID, ForeignKey("tarea.id", ondelete="CASCADE"), nullable=False)
    autor_id: Mapped[UUID] = mapped_column(PG_UUID, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
```

## State Machine

```
            +------------+
            |  Pendiente |
            +------------+
                 | assignee: start
                 v
            +------------+     assignee: resolve
            | En progreso| ----------------------+
            +------------+                       |
                 | assignee: cancel              v
                 v                        +------------+
            +------------+   assigner:   |  Resuelta  |
            | Cancelada  |   approve --> |  aprobada  |
            +------------+   return      +------------+
                  ^          (devuelta)       |
                  |                         |
                  +-------------------------+
                     assigner: devolver
                     (goes to En progreso)
```

Valid transitions enforced by `TareaService._validar_transicion()`:
- `Pendiente` → `En progreso` (assignee)
- `En progreso` → `Resuelta` (assignee)
- `En progreso` → `Cancelada` (assignee)
- `Resuelta` → `En progreso` (assigner, via `devolver`)
- `Resuelta` + `aprobada=True` (assigner, via `aprobar`)
- Any other transition → `HTTPException(422)`

## Service Layer

```python
class TareaService:
    async def crear(self, data: dict) -> TareaResponseSchema
    async def cambiar_estado(self, tarea_id, nuevo_estado, usuario_id) -> TareaResponseSchema
    async def aprobar(self, tarea_id) -> TareaResponseSchema       # sets aprobada=True, revisada_por/at
    async def devolver(self, tarea_id, observacion: str) -> TareaResponseSchema  # sets devuelta=True, estado->En progreso
    async def delegar(self, tarea_id, nuevo_asignado_id) -> TareaResponseSchema  # asignado_a change, audit
    async def list_mis_tareas(self, page, page_size) -> TareaListResponseSchema
    async def list_admin(self, filtros, page, page_size) -> TareaListResponseSchema
```

Guards in every method: `tarea.tenant_id == self.tenant_id`, soft-delete check, role/permission check at router level.

## Repository Layer

```python
class TareaRepository:
    async def create(self, data: dict) -> Tarea
    async def get_by_id(self, tarea_id: UUID) -> Tarea | None
    async def list_por_tenant(self, page, page_size, estado=None, asignado_a=None, materia_id=None, search=None) -> tuple[list[Tarea], int]
    async def list_por_asignado(self, asignado_a: UUID, page, page_size, estado=None) -> tuple[list[Tarea], int]
    async def update(self, tarea_id: UUID, data: dict) -> Tarea | None
    async def soft_delete(self, tarea_id: UUID) -> Tarea | None

class ComentarioTareaRepository:
    async def create(self, data: dict) -> ComentarioTarea
    async def list_por_tarea(self, tarea_id: UUID, page, page_size) -> tuple[list[ComentarioTarea], int]
    async def soft_delete(self, comentario_id: UUID) -> ComentarioTarea | None
```

## API Contract

| Endpoint | Method | Guard | Body | Response |
|---|---|---|---|---|
| `/api/tareas/` | POST | `tareas:gestionar` | `TareaCreateSchema` | `TareaResponseSchema` (201) |
| `/api/tareas/` | GET | `tareas:gestionar` | Query: `page`, `page_size`, `estado`, `asignado_a`, `materia_id`, `q` | `TareaListResponseSchema` |
| `/api/tareas/{id}` | GET | `tareas:gestionar` | — | `TareaResponseSchema` |
| `/api/tareas/{id}` | PATCH | `tareas:gestionar` | `TareaUpdateSchema` | `TareaResponseSchema` |
| `/api/tareas/{id}` | DELETE | `tareas:gestionar` | — | `TareaResponseSchema` |
| `/api/tareas/mis-tareas` | GET | `tareas:gestionar` | Query: `page`, `page_size`, `estado` | `TareaListResponseSchema` |
| `/api/tareas/{id}/estado` | PATCH | `tareas:gestionar` | `TareaEstadoSchema` | `TareaResponseSchema` |
| `/api/tareas/{id}/aprobar` | POST | `tareas:gestionar` | — | `TareaResponseSchema` |
| `/api/tareas/{id}/devolver` | POST | `tareas:gestionar` | `DevolverTareaSchema` | `TareaResponseSchema` |
| `/api/tareas/{id}/delegar` | POST | `tareas:gestionar` | `DelegarTareaSchema` | `TareaResponseSchema` |
| `/api/tareas/{id}/comentarios` | POST | `tareas:gestionar` | `ComentarioCreateSchema` | `ComentarioResponseSchema` (201) |
| `/api/tareas/{id}/comentarios` | GET | `tareas:gestionar` | Query: `page`, `page_size` | `ComentarioListResponseSchema` |

## Migration Schema

`013_tareas_internas.py` creates:

- `tarea` table with columns above + PK `id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at`
- `comentario_tarea` table with columns above + PK `id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at`
- FKs: `tarea.asignado_a → usuarios.id`, `tarea.asignado_por → usuarios.id`, `tarea.revisada_por → usuarios.id`, `tarea.materia_id → materias.id`, `comentario_tarea.tarea_id → tarea.id`, `comentario_tarea.autor_id → usuarios.id`
- Indexes: `ix_tarea_tenant_estado`, `ix_tarea_asignado_estado`, `ix_tarea_materia`, `ix_comentario_tarea_tarea`

## Index Strategy

| Index | Columns | Purpose |
|---|---|---|
| `ix_tarea_tenant_estado` | `(tenant_id, estado)` | Admin filtering by state |
| `ix_tarea_asignado_estado` | `(tenant_id, asignado_a, estado)` | "My tasks" view |
| `ix_tarea_materia` | `(tenant_id, materia_id)` | Filter by materia |
| `ix_comentario_tarea_tarea` | `(tarea_id)` | Load comments per task |

## Audit Action Types

Add to `AuditAction`:
- `TAREA_CREAR`
- `TAREA_ACTUALIZAR`
- `TAREA_ELIMINAR`
- `TAREA_ESTADO_CAMBIAR`
- `TAREA_APROBAR`
- `TAREA_DEVOLVER`
- `TAREA_DELEGAR`
- `TAREA_COMENTAR`
- `TAREA_COMENTARIO_ELIMINAR`

## Error Handling

| Scenario | HTTP | Detail |
|---|---|---|
| Invalid state transition | 422 | `"Transición de estado inválida: {origen} → {destino}"` |
| Task not found | 404 | `"Tarea no encontrada"` |
| Unauthorized actor | 403 | `"No tenés permiso para modificar esta tarea"` |
| Comment not found | 404 | `"Comentario no encontrado"` |
| Approve non-Resuelta | 422 | `"Solo se puede aprobar una tarea Resuelta"` |
| Return non-Resuelta | 422 | `"Solo se puede devolver una tarea Resuelta"` |

## Migration / Rollout

No data migration required — new tables. Rollback: reverse migration drops tables. Feature flag not needed; permission `tareas:gestionar` controls access.

## Open Questions

- None — pre-approved decisions cover all gaps.
