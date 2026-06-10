"""008_calificacion_umbral

C-10: Calificaciones por actividad y umbral de aprobación por asignación.

Schema changes:
- calificaciones: nota por alumno × actividad × materia (numérica y/o textual),
  campo aprobado derivado persistido, scope aislado por docente (RN-04).
- umbrales_materia: umbral % y valores textuales aprobatorios por asignación
  docente en una materia (RN-03).
- Índices de lookup eficiente por scope, tenant y entrada_padron.
- Seed permisos: calificaciones:importar (PROFESOR propio, COORDINADOR global),
  calificaciones:ver (PROFESOR propio, COORDINADOR global),
  calificaciones:vaciar (PROFESOR propio).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008_calificacion_umbral"
down_revision: Union[str, Sequence[str], None] = (
    "007_padron",
    "007_slot_encuentro_instancia_guardia",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Tabla calificaciones
    # ------------------------------------------------------------------
    op.create_table(
        "calificaciones",
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
            "entrada_padron_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("entradas_padron.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materias.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "usuario_importador_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("actividad", sa.String(255), nullable=False),
        sa.Column("nota_numerica", sa.Float(), nullable=True),
        sa.Column("nota_textual", sa.String(100), nullable=True),
        sa.Column("aprobado", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("origen", sa.String(20), nullable=False, server_default="Importado"),
        sa.Column(
            "importado_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
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
        sa.UniqueConstraint(
            "tenant_id",
            "entrada_padron_id",
            "materia_id",
            "actividad",
            "usuario_importador_id",
            name="uq_calificacion_scope",
        ),
    )

    op.create_index(
        "ix_calificaciones_tenant_materia",
        "calificaciones",
        ["tenant_id", "materia_id"],
    )
    op.create_index(
        "ix_calificaciones_entrada_padron",
        "calificaciones",
        ["entrada_padron_id"],
    )
    op.create_index(
        "ix_calificaciones_scope",
        "calificaciones",
        ["tenant_id", "usuario_importador_id", "materia_id"],
    )

    # ------------------------------------------------------------------
    # 2. Tabla umbrales_materia
    # ------------------------------------------------------------------
    op.create_table(
        "umbrales_materia",
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
            "asignacion_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("asignaciones.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materias.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("umbral_pct", sa.Integer(), nullable=False, server_default="60"),
        sa.Column(
            "valores_aprobatorios",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default='["Satisfactorio", "Supera lo esperado"]',
        ),
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
        sa.UniqueConstraint(
            "tenant_id",
            "asignacion_id",
            "materia_id",
            name="uq_umbral_asignacion_materia",
        ),
    )

    op.create_index(
        "ix_umbrales_materia_tenant_materia",
        "umbrales_materia",
        ["tenant_id", "materia_id"],
    )
    op.create_index(
        "ix_umbrales_materia_asignacion",
        "umbrales_materia",
        ["asignacion_id"],
    )

    # ------------------------------------------------------------------
    # 3. Seed permisos: calificaciones:importar, :ver, :vaciar
    # ------------------------------------------------------------------
    conn = op.get_bind()
    tenant_id = conn.execute(
        sa.text("SELECT id FROM tenants ORDER BY created_at LIMIT 1")
    ).scalar()

    if tenant_id is None:
        return

    tid = str(tenant_id)
    tid_param = sa.bindparam("tid", type_=postgresql.UUID(as_uuid=False))

    permisos = [
        (
            "calificaciones:importar",
            "Importar calificaciones (C-10)",
            "calificaciones",
            "Importar calificaciones desde archivo LMS y configurar umbral",
        ),
        (
            "calificaciones:ver",
            "Ver calificaciones (C-10)",
            "calificaciones",
            "Ver calificaciones, rankings y reportes de finalización",
        ),
        (
            "calificaciones:vaciar",
            "Vaciar calificaciones (C-10)",
            "calificaciones",
            "Eliminar calificaciones importadas propias en una materia (RN-04)",
        ),
    ]

    for codigo, nombre, modulo, descripcion in permisos:
        existing = conn.execute(
            sa.text(
                "SELECT id FROM permisos "
                "WHERE tenant_id = :tid AND codigo = :cod AND deleted_at IS NULL LIMIT 1"
            ).bindparams(tid_param, sa.bindparam("cod")),
            {"tid": tid, "cod": codigo},
        ).scalar()

        if existing is None:
            conn.execute(
                sa.text(
                    "INSERT INTO permisos (id, tenant_id, codigo, nombre, modulo, descripcion, "
                    "created_at, updated_at) "
                    "VALUES (gen_random_uuid(), :tid, :cod, :nom, :mod, :desc, NOW(), NOW())"
                ).bindparams(
                    tid_param,
                    sa.bindparam("cod"),
                    sa.bindparam("nom"),
                    sa.bindparam("mod"),
                    sa.bindparam("desc"),
                ),
                {"tid": tid, "cod": codigo, "nom": nombre, "mod": modulo, "desc": descripcion},
            )

    def _seed_rol_permiso(rol_codigo: str, perm_codigo: str, es_propio: bool) -> None:
        conn.execute(
            sa.text(
                "INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, es_propio, "
                "created_at, updated_at) "
                "SELECT gen_random_uuid(), r.tenant_id, r.id, p.id, :propio, NOW(), NOW() "
                "FROM roles r, permisos p "
                "WHERE r.tenant_id = :tid AND r.codigo = :rol "
                "AND p.tenant_id = :tid AND p.codigo = :perm "
                "AND NOT EXISTS ("
                "  SELECT 1 FROM rol_permiso rp2 "
                "  WHERE rp2.rol_id = r.id AND rp2.permiso_id = p.id AND rp2.deleted_at IS NULL"
                ")"
            ).bindparams(
                tid_param,
                sa.bindparam("rol"),
                sa.bindparam("perm"),
                sa.bindparam("propio"),
            ),
            {"tid": tid, "rol": rol_codigo, "perm": perm_codigo, "propio": es_propio},
        )

    # calificaciones:importar — PROFESOR (propio), COORDINADOR (global)
    _seed_rol_permiso("PROFESOR", "calificaciones:importar", True)
    _seed_rol_permiso("COORDINADOR", "calificaciones:importar", False)

    # calificaciones:ver — PROFESOR (propio), COORDINADOR (global)
    _seed_rol_permiso("PROFESOR", "calificaciones:ver", True)
    _seed_rol_permiso("COORDINADOR", "calificaciones:ver", False)

    # calificaciones:vaciar — solo PROFESOR (propio); COORDINADOR no vacía ajeno
    _seed_rol_permiso("PROFESOR", "calificaciones:vaciar", True)


def downgrade() -> None:
    op.drop_index("ix_umbrales_materia_asignacion", table_name="umbrales_materia")
    op.drop_index("ix_umbrales_materia_tenant_materia", table_name="umbrales_materia")
    op.drop_table("umbrales_materia")

    op.drop_index("ix_calificaciones_scope", table_name="calificaciones")
    op.drop_index("ix_calificaciones_entrada_padron", table_name="calificaciones")
    op.drop_index("ix_calificaciones_tenant_materia", table_name="calificaciones")
    op.drop_table("calificaciones")
    # Los permisos seedeados quedan como huérfanos para preservar integridad.
