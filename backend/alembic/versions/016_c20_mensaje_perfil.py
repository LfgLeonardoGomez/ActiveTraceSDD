"""016_c20_mensaje_perfil

C-20: Perfil de usuario editable y mensajería interna.

Schema changes:
- mensaje: tabla de mensajes internos entre usuarios con parent_id self-FK.

Rollback: drop table mensaje.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "016_c20_mensaje_perfil"
down_revision: Union[str, Sequence[str], None] = "015_c18_liquidaciones"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mensaje",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "remitente_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "destinatario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("asunto", sa.String(500), nullable=False),
        sa.Column("cuerpo", sa.Text, nullable=False),
        sa.Column(
            "parent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mensaje.id", ondelete="RESTRICT"),
            nullable=True,
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
    op.create_index(
        "ix_mensaje_tenant_destinatario_parent_deleted",
        "mensaje",
        ["tenant_id", "destinatario_id", "parent_id", "deleted_at"],
    )
    op.create_index(
        "ix_mensaje_tenant_parent_created",
        "mensaje",
        ["tenant_id", "parent_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_mensaje_tenant_parent_created", table_name="mensaje")
    op.drop_index("ix_mensaje_tenant_destinatario_parent_deleted", table_name="mensaje")
    op.drop_table("mensaje")
