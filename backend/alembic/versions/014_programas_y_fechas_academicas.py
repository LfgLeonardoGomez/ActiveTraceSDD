"""014_programas_y_fechas_academicas

C-17: Tablas de programas de materia y fechas académicas.

Schema changes:
- programa_materia: documentos oficiales de programa por materia×carrera×cohorte.
- fecha_academica: calendarización de evaluaciones por materia×cohorte.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "014_programas_y_fechas_academicas"
down_revision: Union[str, Sequence[str], None] = "013_tareas_internas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Tabla programa_materia
    # ------------------------------------------------------------------
    op.create_table(
        "programa_materia",
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
            "carrera_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("carreras.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "cohorte_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cohortes.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("referencia_archivo", sa.Text(), nullable=False),
        sa.Column(
            "cargado_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
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
        "ix_programa_materia_tenant_combinacion",
        "programa_materia",
        ["tenant_id", "materia_id", "carrera_id", "cohorte_id"],
        unique=True,
        postgresql_where="deleted_at IS NULL",
    )
    op.create_index(
        "ix_programa_materia_materia", "programa_materia", ["tenant_id", "materia_id"]
    )

    # ------------------------------------------------------------------
    # 2. Tabla fecha_academica
    # ------------------------------------------------------------------
    op.create_table(
        "fecha_academica",
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
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("periodo", sa.String(20), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("titulo", sa.String(300), nullable=False),
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
        "ix_fecha_academica_materia", "fecha_academica", ["tenant_id", "materia_id"]
    )
    op.create_index(
        "ix_fecha_academica_materia_cohorte",
        "fecha_academica",
        ["tenant_id", "materia_id", "cohorte_id"],
    )
    op.create_index(
        "ix_fecha_academica_fecha", "fecha_academica", ["tenant_id", "fecha"]
    )

    # ------------------------------------------------------------------
    # 3. Permiso estructura:ver (si no existe)
    # ------------------------------------------------------------------
    op.execute(
        """
        INSERT INTO permisos (id, codigo, nombre, descripcion)
        SELECT gen_random_uuid(), 'estructura:ver', 'Ver estructura académica', 'Permite visualizar programas y fechas académicas'
        WHERE NOT EXISTS (
            SELECT 1 FROM permisos WHERE codigo = 'estructura:ver'
        );
        """
    )
    op.execute(
        """
        INSERT INTO rol_permiso (rol_id, permiso_id)
        SELECT r.id, p.id
        FROM roles r
        CROSS JOIN permisos p
        WHERE p.codigo = 'estructura:ver'
          AND r.codigo IN ('ADMIN', 'COORDINADOR', 'PROFESOR')
          AND NOT EXISTS (
              SELECT 1 FROM rol_permiso rp
              WHERE rp.rol_id = r.id AND rp.permiso_id = p.id
          );
        """
    )


def downgrade() -> None:
    op.drop_index("ix_fecha_academica_fecha", table_name="fecha_academica")
    op.drop_index("ix_fecha_academica_materia_cohorte", table_name="fecha_academica")
    op.drop_index("ix_fecha_academica_materia", table_name="fecha_academica")
    op.drop_table("fecha_academica")

    op.drop_index("ix_programa_materia_materia", table_name="programa_materia")
    op.drop_index(
        "ix_programa_materia_tenant_combinacion", table_name="programa_materia"
    )
    op.drop_table("programa_materia")
