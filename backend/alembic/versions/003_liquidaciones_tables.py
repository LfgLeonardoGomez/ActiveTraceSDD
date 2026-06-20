"""liquidaciones_tables

Crea todas las tablas del módulo de liquidaciones (C-18):
  - salarios_base
  - salarios_plus
  - materia_grupo_plus
  - facturas
  - liquidaciones
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003_liquidaciones_tables"
down_revision: Union[str, Sequence[str], None] = "002_grant_admin_all_permissions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ================================================================
    # salarios_base
    # Columnas mixin: id, tenant_id, created_at, updated_at, deleted_at
    # Columnas propias: rol, monto, desde, hasta
    # ================================================================
    op.create_table(
        "salarios_base",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
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
        sa.Column("rol", sa.String(50), nullable=False),
        sa.Column("monto", sa.Numeric(18, 2), nullable=False),
        sa.Column("desde", sa.Date(), nullable=False),
        sa.Column("hasta", sa.Date(), nullable=True),
    )
    op.create_index(
        "ix_salarios_base_tenant_rol_desde",
        "salarios_base",
        ["tenant_id", "rol", "desde"],
    )

    # ================================================================
    # salarios_plus
    # Columnas mixin: id, tenant_id, created_at, updated_at, deleted_at
    # Columnas propias: grupo, rol, descripcion, monto, tope_acumulacion, desde, hasta
    # ================================================================
    op.create_table(
        "salarios_plus",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
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
        sa.Column("grupo", sa.String(100), nullable=False),
        sa.Column("rol", sa.String(50), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("monto", sa.Numeric(18, 2), nullable=False),
        sa.Column(
            "tope_acumulacion",
            sa.Numeric(10, 2),
            nullable=True,
            comment="NULL = sin tope. Positivo = máximo de comisiones del grupo que acumulan plus.",
        ),
        sa.Column("desde", sa.Date(), nullable=False),
        sa.Column("hasta", sa.Date(), nullable=True),
    )
    op.create_index(
        "ix_salarios_plus_tenant_grupo_rol_desde",
        "salarios_plus",
        ["tenant_id", "grupo", "rol", "desde"],
    )

    # ================================================================
    # materia_grupo_plus
    # FK: materias.id
    # Columnas mixin: id, tenant_id, created_at, updated_at, deleted_at
    # Columnas propias: materia_id, grupo, desde, hasta
    # ================================================================
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
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materias.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("grupo", sa.String(100), nullable=False),
        sa.Column("desde", sa.Date(), nullable=False),
        sa.Column("hasta", sa.Date(), nullable=True),
    )
    op.create_index(
        "ix_mgp_tenant_materia_desde",
        "materia_grupo_plus",
        ["tenant_id", "materia_id", "desde"],
    )
    op.create_index(
        "ix_mgp_tenant_grupo",
        "materia_grupo_plus",
        ["tenant_id", "grupo"],
    )

    # ================================================================
    # facturas
    # FK: usuarios.id
    # Columnas mixin: id, tenant_id, created_at, updated_at, deleted_at
    # Columnas propias: usuario_id, periodo, detalle, referencia_archivo,
    #                   tamano_kb, estado, cargada_at, abonada_at
    # ================================================================
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
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "periodo",
            sa.String(7),
            nullable=False,
            comment="Formato AAAA-MM (ej: 2026-03)",
        ),
        sa.Column(
            "detalle",
            sa.Text(),
            nullable=True,
            comment="Texto libre de descripción del servicio facturado",
        ),
        sa.Column(
            "referencia_archivo",
            sa.Text(),
            nullable=False,
            comment="Puntero opaco al archivo en el storage (D6). NO guarda binario en DB.",
        ),
        sa.Column(
            "tamano_kb",
            sa.Numeric(10, 2),
            nullable=True,
            comment="Tamaño del archivo en kilobytes",
        ),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("cargada_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("abonada_at", sa.DateTime(timezone=True), nullable=True),
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

    # ================================================================
    # liquidaciones
    # FK: cohortes.id, usuarios.id (x2)
    # Columnas mixin: id, tenant_id, created_at, updated_at, deleted_at
    # Columnas propias: cohorte_id, periodo, usuario_id, rol, monto_base,
    #                   monto_plus, total, es_nexo, excluido_por_factura,
    #                   estado, cerrada_at, cerrada_por_usuario_id, detalle_plus
    # ================================================================
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
        sa.Column(
            "cohorte_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cohortes.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "periodo",
            sa.String(7),
            nullable=False,
            comment="Formato AAAA-MM (ej: 2026-03)",
        ),
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
        sa.Column("es_nexo", sa.Boolean(), nullable=False),
        sa.Column(
            "excluido_por_factura",
            sa.Boolean(),
            nullable=False,
            comment="Snapshot del flag facturador al momento del cierre (D4)",
        ),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("cerrada_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "cerrada_por_usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "detalle_plus",
            sa.Text(),
            nullable=True,
            comment="JSON serializado con desglose de plus por grupo",
        ),
    )
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


def downgrade() -> None:
    op.drop_table("liquidaciones")
    op.drop_table("facturas")
    op.drop_table("materia_grupo_plus")
    op.drop_table("salarios_plus")
    op.drop_table("salarios_base")
