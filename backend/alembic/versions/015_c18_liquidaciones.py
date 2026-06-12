"""015_c18_liquidaciones

C-18: Módulo de liquidaciones y honorarios docentes.

Schema changes (una sola migración, decisión D7):
- salarios_base: monto base por rol docente con vigencia temporal.
- salarios_plus: monto plus por (grupo × rol) con tope opcional (PA-23).
- materia_grupo_plus: mapeo materia → grupo de plus con vigencia (PA-22).
- liquidaciones: filas de honorarios por (usuario, rol, cohorte, periodo).
- facturas: comprobantes de docentes facturantes con referencia opaca al archivo.

Rollback guard (D7): el downgrade() aborta si existen liquidaciones Cerradas.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "015_c18_liquidaciones"
down_revision: Union[str, Sequence[str], None] = "014_programas_y_fechas_academicas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. salarios_base
    # ------------------------------------------------------------------
    op.create_table(
        "salarios_base",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("rol", sa.String(50), nullable=False),
        sa.Column("monto", sa.Numeric(18, 2), nullable=False),
        sa.Column("desde", sa.Date, nullable=False),
        sa.Column("hasta", sa.Date, nullable=True),
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
        "ix_salarios_base_tenant_rol_desde",
        "salarios_base",
        ["tenant_id", "rol", sa.text("desde DESC")],
    )

    # ------------------------------------------------------------------
    # 2. salarios_plus
    # ------------------------------------------------------------------
    op.create_table(
        "salarios_plus",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("grupo", sa.String(100), nullable=False),
        sa.Column("rol", sa.String(50), nullable=False),
        sa.Column("descripcion", sa.Text, nullable=True),
        sa.Column("monto", sa.Numeric(18, 2), nullable=False),
        sa.Column(
            "tope_acumulacion",
            sa.Numeric(10, 2),
            nullable=True,
            comment="NULL=sin tope; positivo=max comisiones que acumulan plus",
        ),
        sa.Column("desde", sa.Date, nullable=False),
        sa.Column("hasta", sa.Date, nullable=True),
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
        "ix_salarios_plus_tenant_grupo_rol_desde",
        "salarios_plus",
        ["tenant_id", "grupo", "rol", sa.text("desde DESC")],
    )

    # ------------------------------------------------------------------
    # 3. materia_grupo_plus
    # ------------------------------------------------------------------
    op.create_table(
        "materia_grupo_plus",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materias.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("grupo", sa.String(100), nullable=False),
        sa.Column("desde", sa.Date, nullable=False),
        sa.Column("hasta", sa.Date, nullable=True),
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
        "ix_mgp_tenant_materia_desde",
        "materia_grupo_plus",
        ["tenant_id", "materia_id", sa.text("desde DESC")],
    )
    op.create_index(
        "ix_mgp_tenant_grupo",
        "materia_grupo_plus",
        ["tenant_id", "grupo"],
    )

    # ------------------------------------------------------------------
    # 4. liquidaciones
    # ------------------------------------------------------------------
    op.create_table(
        "liquidaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "cohorte_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cohortes.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("periodo", sa.String(7), nullable=False),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("rol", sa.String(50), nullable=False),
        sa.Column("monto_base", sa.Numeric(18, 2), nullable=False),
        sa.Column("monto_plus", sa.Numeric(18, 2), nullable=False),
        sa.Column("total", sa.Numeric(18, 2), nullable=False),
        sa.Column("es_nexo", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("excluido_por_factura", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Abierta"),
        sa.Column("cerrada_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "cerrada_por_usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("detalle_plus", sa.Text, nullable=True),
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
    # Índice parcial único por (tenant, cohorte, periodo) donde deleted_at IS NULL
    op.create_index(
        "ix_liquidaciones_tenant_cohorte_periodo",
        "liquidaciones",
        ["tenant_id", "cohorte_id", "periodo"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_liquidaciones_tenant_estado",
        "liquidaciones",
        ["tenant_id", "estado"],
    )

    # ------------------------------------------------------------------
    # 5. facturas
    # ------------------------------------------------------------------
    op.create_table(
        "facturas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("periodo", sa.String(7), nullable=False),
        sa.Column("detalle", sa.Text, nullable=True),
        sa.Column("referencia_archivo", sa.Text, nullable=False),
        sa.Column("tamano_kb", sa.Numeric(10, 2), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Pendiente"),
        sa.Column("cargada_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("abonada_at", sa.DateTime(timezone=True), nullable=True),
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
        "ix_facturas_tenant_usuario_periodo",
        "facturas",
        ["tenant_id", "usuario_id", "periodo"],
    )
    op.create_index(
        "ix_facturas_tenant_estado",
        "facturas",
        ["tenant_id", "estado"],
    )


def downgrade() -> None:
    """Revierte todas las tablas de C-18.

    Guard (D7): aborta si existen liquidaciones con estado 'Cerrada'.
    La existencia de datos cerrados indica que hay histórico contable
    que no puede eliminarse sin acción manual del DBA.
    """
    connection = op.get_bind()
    result = connection.execute(
        sa.text(
            "SELECT COUNT(*) FROM liquidaciones WHERE estado = 'Cerrada'"
        )
    )
    count = result.scalar()
    if count and count > 0:
        raise Exception(
            f"Downgrade abortado: existen {count} liquidaciones con estado='Cerrada'. "
            "Exportar o truncar manualmente antes de ejecutar el downgrade."
        )

    op.drop_index("ix_facturas_tenant_estado", table_name="facturas")
    op.drop_index("ix_facturas_tenant_usuario_periodo", table_name="facturas")
    op.drop_table("facturas")

    op.drop_index("ix_liquidaciones_tenant_estado", table_name="liquidaciones")
    op.drop_index("ix_liquidaciones_tenant_cohorte_periodo", table_name="liquidaciones")
    op.drop_table("liquidaciones")

    op.drop_index("ix_mgp_tenant_grupo", table_name="materia_grupo_plus")
    op.drop_index("ix_mgp_tenant_materia_desde", table_name="materia_grupo_plus")
    op.drop_table("materia_grupo_plus")

    op.drop_index("ix_salarios_plus_tenant_grupo_rol_desde", table_name="salarios_plus")
    op.drop_table("salarios_plus")

    op.drop_index("ix_salarios_base_tenant_rol_desde", table_name="salarios_base")
    op.drop_table("salarios_base")
