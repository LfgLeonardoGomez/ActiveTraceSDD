"""010_evaluaciones

C-14: Tablas de evaluaciones y coloquios.

Schema changes:
- evaluacion: convocatoria formal (coloquio, parcial, recuperatorio)
- evaluacion_candidato: padrón de alumnos habilitados por convocatoria
- reserva_evaluacion: turno reservado por alumno (Activa/Cancelada)
- resultado_evaluacion: nota final del alumno en la convocatoria
- permisos RBAC: coloquios:gestionar, coloquios:reservar, coloquios:ver
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010_evaluaciones"
down_revision: Union[str, Sequence[str], None] = "009_comunicacion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Tabla evaluacion
    # ------------------------------------------------------------------
    op.create_table(
        "evaluacion",
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
        sa.Column(
            "cohorte_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cohortes.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column("instancia", sa.String(200), nullable=False),
        sa.Column("dias_disponibles", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("cupo_por_dia", sa.Integer(), nullable=False, server_default="1"),
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
    op.create_index("ix_evaluacion_tenant", "evaluacion", ["tenant_id"])
    op.create_index("ix_evaluacion_materia", "evaluacion", ["tenant_id", "materia_id"])
    op.create_index("ix_evaluacion_cohorte", "evaluacion", ["tenant_id", "cohorte_id"])

    # ------------------------------------------------------------------
    # 2. Tabla evaluacion_candidato (asociativa, sin soft delete)
    # ------------------------------------------------------------------
    op.create_table(
        "evaluacion_candidato",
        sa.Column(
            "evaluacion_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("evaluacion.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "alumno_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            primary_key=True,
            nullable=False,
        ),
    )
    op.create_index(
        "ix_evaluacion_candidato_evaluacion", "evaluacion_candidato", ["evaluacion_id"]
    )
    op.create_index(
        "ix_evaluacion_candidato_alumno", "evaluacion_candidato", ["alumno_id"]
    )

    # ------------------------------------------------------------------
    # 3. Tabla reserva_evaluacion
    # ------------------------------------------------------------------
    op.create_table(
        "reserva_evaluacion",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "evaluacion_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("evaluacion.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "alumno_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("fecha_hora", sa.DateTime(timezone=True), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Activa"),
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
        "ix_reserva_evaluacion_evaluacion", "reserva_evaluacion", ["evaluacion_id"]
    )
    op.create_index(
        "ix_reserva_evaluacion_alumno", "reserva_evaluacion", ["alumno_id"]
    )
    op.create_index(
        "ix_reserva_evaluacion_tenant_estado",
        "reserva_evaluacion",
        ["tenant_id", "estado"],
    )

    # ------------------------------------------------------------------
    # 4. Tabla resultado_evaluacion
    # ------------------------------------------------------------------
    op.create_table(
        "resultado_evaluacion",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "evaluacion_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("evaluacion.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "alumno_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("nota_final", sa.Text(), nullable=True),
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
        "uq_resultado_evaluacion", "resultado_evaluacion", ["evaluacion_id", "alumno_id"]
    )
    op.create_index(
        "ix_resultado_evaluacion_evaluacion", "resultado_evaluacion", ["evaluacion_id"]
    )

    # ------------------------------------------------------------------
    # 5. Seed RBAC: 3 permisos nuevos + asociaciones por rol
    # ------------------------------------------------------------------
    conn = op.get_bind()
    tenant_id = conn.execute(
        sa.text("SELECT id FROM tenants ORDER BY created_at LIMIT 1")
    ).scalar()

    if tenant_id is None:
        return

    tid = str(tenant_id)

    # Insertar permisos si no existen
    for codigo in ("coloquios:gestionar", "coloquios:reservar", "coloquios:ver"):
        exists = conn.execute(
            sa.text(
                f"SELECT COUNT(*) FROM permisos "
                f"WHERE tenant_id = '{tid}'::uuid AND codigo = '{codigo}'"
            )
        ).scalar()
        if exists == 0:
            op.execute(
                sa.text(
                    f"INSERT INTO permisos (id, tenant_id, codigo, created_at, updated_at) "
                    f"VALUES (gen_random_uuid(), '{tid}'::uuid, '{codigo}', NOW(), NOW())"
                )
            )

    # Matriz de asignación: rol → [permiso, es_propio]
    rbac_matrix = [
        ("COORDINADOR", "coloquios:gestionar", False),
        ("ADMIN",        "coloquios:gestionar", False),
        ("ALUMNO",       "coloquios:reservar",  False),
        ("TUTOR",        "coloquios:ver",        False),
        ("PROFESOR",     "coloquios:ver",        False),
        ("COORDINADOR",  "coloquios:ver",        False),
        ("ADMIN",        "coloquios:ver",        False),
    ]

    for rol_codigo, permiso_codigo, es_propio in rbac_matrix:
        propio_str = "true" if es_propio else "false"
        existing = conn.execute(
            sa.text(
                f"SELECT COUNT(*) FROM rol_permiso rp "
                f"JOIN roles r ON rp.rol_id = r.id "
                f"JOIN permisos p ON rp.permiso_id = p.id "
                f"WHERE r.tenant_id = '{tid}'::uuid AND r.codigo = '{rol_codigo}' "
                f"AND p.tenant_id = '{tid}'::uuid AND p.codigo = '{permiso_codigo}' "
                f"AND rp.deleted_at IS NULL"
            )
        ).scalar()
        if existing == 0:
            op.execute(
                sa.text(
                    f"INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, es_propio, created_at, updated_at) "
                    f"SELECT gen_random_uuid(), '{tid}'::uuid, r.id, p.id, {propio_str}, NOW(), NOW() "
                    f"FROM roles r, permisos p "
                    f"WHERE r.tenant_id = '{tid}'::uuid AND r.codigo = '{rol_codigo}' "
                    f"AND p.tenant_id = '{tid}'::uuid AND p.codigo = '{permiso_codigo}'"
                )
            )


def downgrade() -> None:
    op.drop_index("ix_resultado_evaluacion_evaluacion", table_name="resultado_evaluacion")
    op.drop_constraint("uq_resultado_evaluacion", "resultado_evaluacion", type_="unique")
    op.drop_table("resultado_evaluacion")

    op.drop_index("ix_reserva_evaluacion_tenant_estado", table_name="reserva_evaluacion")
    op.drop_index("ix_reserva_evaluacion_alumno", table_name="reserva_evaluacion")
    op.drop_index("ix_reserva_evaluacion_evaluacion", table_name="reserva_evaluacion")
    op.drop_table("reserva_evaluacion")

    op.drop_index("ix_evaluacion_candidato_alumno", table_name="evaluacion_candidato")
    op.drop_index("ix_evaluacion_candidato_evaluacion", table_name="evaluacion_candidato")
    op.drop_table("evaluacion_candidato")

    op.drop_index("ix_evaluacion_cohorte", table_name="evaluacion")
    op.drop_index("ix_evaluacion_materia", table_name="evaluacion")
    op.drop_index("ix_evaluacion_tenant", table_name="evaluacion")
    op.drop_table("evaluacion")
