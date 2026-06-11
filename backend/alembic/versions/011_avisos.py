"""011_avisos

C-15: Tablas de avisos y acknowledgment.

Schema changes:
- aviso: anuncio dirigido a segmentos de usuarios
- acknowledgment_aviso: confirmación de lectura por usuario
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "011_avisos"
down_revision: Union[str, Sequence[str], None] = "010_evaluaciones"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Tabla aviso
    # ------------------------------------------------------------------
    op.create_table(
        "aviso",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("alcance", sa.String(30), nullable=False),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materias.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "cohorte_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cohortes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("rol_destino", sa.String(30), nullable=True),
        sa.Column("severidad", sa.String(30), nullable=False),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column("inicio_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fin_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "requiere_ack", sa.Boolean(), nullable=False, server_default="false"
        ),
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
    op.create_index("ix_aviso_tenant", "aviso", ["tenant_id"])
    op.create_index(
        "ix_aviso_tenant_activo_vigencia",
        "aviso",
        ["tenant_id", "activo", "inicio_en", "fin_en"],
    )
    op.create_index(
        "ix_aviso_alcance",
        "aviso",
        ["tenant_id", "alcance", "materia_id", "cohorte_id"],
    )

    # ------------------------------------------------------------------
    # 2. Tabla acknowledgment_aviso
    # ------------------------------------------------------------------
    op.create_table(
        "acknowledgment_aviso",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "aviso_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("aviso.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("confirmado_at", sa.DateTime(timezone=True), nullable=False),
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
    op.create_unique_constraint(
        "uq_ack_aviso_usuario", "acknowledgment_aviso", ["aviso_id", "usuario_id"]
    )
    op.create_index(
        "ix_ack_aviso_aviso", "acknowledgment_aviso", ["aviso_id"]
    )
    op.create_index(
        "ix_ack_aviso_usuario", "acknowledgment_aviso", ["usuario_id"]
    )


def downgrade() -> None:
    op.drop_table("acknowledgment_aviso")
    op.drop_table("aviso")
