"""013_tareas_internas

C-16: Tablas de tareas internas y comentarios.

Schema changes:
- tarea: tareas asignadas entre coordinadores y docentes.
- comentario_tarea: comentarios sobre tareas.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "013_tareas_internas"
down_revision: Union[str, Sequence[str], None] = "012_aviso_acknowledgment"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Tabla tarea
    # ------------------------------------------------------------------
    op.create_table(
        "tarea",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("criterio_cierre", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(30), nullable=False, server_default="Pendiente"),
        sa.Column("aprobada", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("devuelta", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "asignado_a",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "asignado_por",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "revisada_por",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("revisada_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materias.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("contexto_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_tarea_tenant_estado", "tarea", ["tenant_id", "estado"])
    op.create_index(
        "ix_tarea_asignado_estado", "tarea", ["tenant_id", "asignado_a", "estado"]
    )
    op.create_index("ix_tarea_materia", "tarea", ["tenant_id", "materia_id"])

    # ------------------------------------------------------------------
    # 2. Tabla comentario_tarea
    # ------------------------------------------------------------------
    op.create_table(
        "comentario_tarea",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "tarea_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tarea.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "autor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("contenido", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_comentario_tarea_tarea", "comentario_tarea", ["tarea_id"])


def downgrade() -> None:
    op.drop_index("ix_comentario_tarea_tarea", table_name="comentario_tarea")
    op.drop_table("comentario_tarea")

    op.drop_index("ix_tarea_materia", table_name="tarea")
    op.drop_index("ix_tarea_asignado_estado", table_name="tarea")
    op.drop_index("ix_tarea_tenant_estado", table_name="tarea")
    op.drop_table("tarea")
