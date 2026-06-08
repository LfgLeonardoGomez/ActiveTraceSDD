"""004_audit_log

C-05: AuditLog append-only con trigger DB que bloquea UPDATE y DELETE.

Schema changes:
- audit_log: nueva tabla E-AUD
- deny_audit_log_mutation: función PL/pgSQL que lanza excepción en UPDATE/DELETE
- trg_audit_log_immutable: trigger BEFORE UPDATE OR DELETE sobre audit_log
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_audit_log"
down_revision: Union[str, Sequence[str], None] = "002_rbac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea la tabla audit_log con trigger de inmutabilidad."""
    op.create_table(
        "audit_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "fecha_hora",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "impersonado_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # FK lógica a materias — constraint añadido en C-06
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("accion", sa.String(100), nullable=False),
        sa.Column("detalle", postgresql.JSONB(), nullable=True),
        sa.Column("filas_afectadas", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ip", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
    )
    op.create_index("ix_audit_log_tenant_id", "audit_log", ["tenant_id"])
    op.create_index("ix_audit_log_actor_id", "audit_log", ["actor_id"])
    op.create_index("ix_audit_log_fecha_hora", "audit_log", ["fecha_hora"])

    op.execute("""
        CREATE OR REPLACE FUNCTION deny_audit_log_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log is immutable: % on row % is not allowed', TG_OP, OLD.id;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_audit_log_immutable
        BEFORE UPDATE OR DELETE ON audit_log
        FOR EACH ROW EXECUTE FUNCTION deny_audit_log_mutation();
    """)


def downgrade() -> None:
    """Elimina trigger, función y tabla audit_log."""
    op.execute("DROP TRIGGER IF EXISTS trg_audit_log_immutable ON audit_log;")
    op.execute("DROP FUNCTION IF EXISTS deny_audit_log_mutation();")
    op.drop_index("ix_audit_log_fecha_hora", table_name="audit_log")
    op.drop_index("ix_audit_log_actor_id", table_name="audit_log")
    op.drop_index("ix_audit_log_tenant_id", table_name="audit_log")
    op.drop_table("audit_log")
