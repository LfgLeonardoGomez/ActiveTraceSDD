"""005_carrera_cohorte_materia

C-06: Estructura académica base — Carrera, Cohorte, Materia.

Schema changes:
- carreras: nueva tabla (id, tenant_id, codigo, nombre, estado, timestamps)
- cohortes: nueva tabla (id, tenant_id, carrera_id FK, nombre, anio, vig_desde, vig_hasta, estado, timestamps)
- materias: nueva tabla (id, tenant_id, codigo, nombre, estado, timestamps)

Índices únicos parciales (WHERE deleted_at IS NULL):
- carreras: (tenant_id, codigo)
- cohortes: (tenant_id, carrera_id, nombre)
- materias: (tenant_id, codigo)

También agrega FK audit_log.materia_id → materias.id (prometida en 004_audit_log).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_carrera_cohorte_materia"
down_revision: Union[str, Sequence[str], None] = "004_audit_log"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea tablas carreras, cohortes y materias con índices parciales."""

    # ------------------------------------------------------------------
    # 1. Tabla carreras
    # ------------------------------------------------------------------
    op.create_table(
        "carreras",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("codigo", sa.Text(), nullable=False),
        sa.Column("nombre", sa.Text(), nullable=False),
        sa.Column("estado", sa.Text(), nullable=False, server_default="Activa"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index(
        "idx_carreras_tenant_codigo",
        "carreras",
        ["tenant_id", "codigo"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_carreras_tenant_id", "carreras", ["tenant_id"])

    # ------------------------------------------------------------------
    # 2. Tabla cohortes
    # ------------------------------------------------------------------
    op.create_table(
        "cohortes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "carrera_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("carreras.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("nombre", sa.Text(), nullable=False),
        sa.Column("anio", sa.Integer(), nullable=False),
        sa.Column("vig_desde", sa.Date(), nullable=False),
        sa.Column("vig_hasta", sa.Date(), nullable=True),
        sa.Column("estado", sa.Text(), nullable=False, server_default="Activa"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index(
        "idx_cohortes_tenant_carrera_nombre",
        "cohortes",
        ["tenant_id", "carrera_id", "nombre"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_cohortes_tenant_id", "cohortes", ["tenant_id"])
    op.create_index("ix_cohortes_carrera_id", "cohortes", ["carrera_id"])

    # ------------------------------------------------------------------
    # 3. Tabla materias
    # ------------------------------------------------------------------
    op.create_table(
        "materias",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("codigo", sa.Text(), nullable=False),
        sa.Column("nombre", sa.Text(), nullable=False),
        sa.Column("estado", sa.Text(), nullable=False, server_default="Activa"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index(
        "idx_materias_tenant_codigo",
        "materias",
        ["tenant_id", "codigo"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_materias_tenant_id", "materias", ["tenant_id"])

    # ------------------------------------------------------------------
    # 4. Agregar FK audit_log.materia_id → materias.id (prometida en 004)
    # ------------------------------------------------------------------
    op.create_foreign_key(
        "fk_audit_log_materia_id",
        "audit_log",
        "materias",
        ["materia_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ------------------------------------------------------------------
    # 5. Seed permiso estructura:gestionar en tenant default
    #    (en paralelo con estructura_academica:gestionar que ya existe;
    #     los endpoints de C-06 usan estructura:gestionar)
    # ------------------------------------------------------------------
    conn = op.get_bind()
    tenant_id = conn.execute(
        sa.text("SELECT id FROM tenants ORDER BY created_at LIMIT 1")
    ).scalar()

    if tenant_id is None:
        return

    tenant_id_str = str(tenant_id)

    # Verificar si ya existe el permiso estructura:gestionar
    existing = conn.execute(
        sa.text(
            "SELECT id FROM permisos "
            "WHERE tenant_id = :tid AND codigo = 'estructura:gestionar' "
            "AND deleted_at IS NULL LIMIT 1"
        ),
        {"tid": tenant_id_str},
    ).scalar()

    if existing is None:
        conn.execute(
            sa.text(
                "INSERT INTO permisos (id, tenant_id, codigo, nombre, modulo, descripcion, created_at, updated_at) "
                "VALUES (gen_random_uuid(), :tid::uuid, 'estructura:gestionar', "
                "'Gestionar estructura académica (C-06)', 'estructura', "
                "'Gestionar carreras, cohortes y materias del tenant', NOW(), NOW())"
            ),
            {"tid": tenant_id_str},
        )

    # Asignar al rol ADMIN si no está ya asignado
    conn.execute(
        sa.text(
            "INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, es_propio, created_at, updated_at) "
            "SELECT gen_random_uuid(), :tid::uuid, r.id, p.id, false, NOW(), NOW() "
            "FROM roles r, permisos p "
            "WHERE r.tenant_id = :tid::uuid AND r.codigo = 'ADMIN' "
            "AND p.tenant_id = :tid::uuid AND p.codigo = 'estructura:gestionar' "
            "AND NOT EXISTS ("
            "  SELECT 1 FROM rol_permiso rp2 "
            "  WHERE rp2.rol_id = r.id AND rp2.permiso_id = p.id AND rp2.deleted_at IS NULL"
            ")"
        ),
        {"tid": tenant_id_str},
    )


def downgrade() -> None:
    """Revierte tablas de estructura académica."""
    # Eliminar FK de audit_log primero
    op.drop_constraint("fk_audit_log_materia_id", "audit_log", type_="foreignkey")

    # Índices y tabla materias
    op.drop_index("idx_materias_tenant_codigo", table_name="materias")
    op.drop_index("ix_materias_tenant_id", table_name="materias")
    op.drop_table("materias")

    # Índices y tabla cohortes
    op.drop_index("idx_cohortes_tenant_carrera_nombre", table_name="cohortes")
    op.drop_index("ix_cohortes_tenant_id", table_name="cohortes")
    op.drop_index("ix_cohortes_carrera_id", table_name="cohortes")
    op.drop_table("cohortes")

    # Índices y tabla carreras
    op.drop_index("idx_carreras_tenant_codigo", table_name="carreras")
    op.drop_index("ix_carreras_tenant_id", table_name="carreras")
    op.drop_table("carreras")
