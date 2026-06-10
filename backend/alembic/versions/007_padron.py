"""007_padron

C-09: Padrón versionado de alumnos por materia × cohorte.

Schema changes:
- versiones_padron: nueva tabla (materia_id, cohorte_id, cargado_por, cargado_at,
  activa, origen)
- entradas_padron: nueva tabla (version_id, usuario_id nullable, nombre, apellidos,
  email TEXT ciphertext, comision, regional)
- Índices de lookup eficiente para versión activa y entradas por versión.
- Seed permiso: padron:cargar para PROFESOR (propio) y COORDINADOR (global).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007_padron"
down_revision: Union[str, Sequence[str], None] = "006_usuario_pii_asignacion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Tabla versiones_padron
    # ------------------------------------------------------------------
    op.create_table(
        "versiones_padron",
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
        sa.Column(
            "cargado_por",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "cargado_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("origen", sa.String(20), nullable=False, server_default="manual"),
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
        "ix_versiones_padron_tenant_materia_cohorte",
        "versiones_padron",
        ["tenant_id", "materia_id", "cohorte_id"],
    )
    op.create_index(
        "ix_versiones_padron_activa",
        "versiones_padron",
        ["tenant_id", "materia_id", "cohorte_id", "activa"],
    )

    # ------------------------------------------------------------------
    # 2. Tabla entradas_padron
    # ------------------------------------------------------------------
    op.create_table(
        "entradas_padron",
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
            "version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("versiones_padron.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("apellidos", sa.String(100), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("comision", sa.String(100), nullable=False, server_default=""),
        sa.Column("regional", sa.String(100), nullable=False, server_default=""),
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
        "ix_entradas_padron_version_id", "entradas_padron", ["version_id"]
    )
    op.create_index(
        "ix_entradas_padron_tenant_id", "entradas_padron", ["tenant_id"]
    )
    op.create_index(
        "ix_entradas_padron_usuario_id", "entradas_padron", ["usuario_id"]
    )

    # ------------------------------------------------------------------
    # 3. Seed permiso padron:cargar
    # ------------------------------------------------------------------
    conn = op.get_bind()
    tenant_id = conn.execute(
        sa.text("SELECT id FROM tenants ORDER BY created_at LIMIT 1")
    ).scalar()

    if tenant_id is None:
        return

    tenant_id_str = str(tenant_id)

    # Permiso padron:cargar
    existing = conn.execute(
        sa.text(
            "SELECT id FROM permisos "
            "WHERE tenant_id = :tid AND codigo = 'padron:cargar' "
            "AND deleted_at IS NULL LIMIT 1"
        ).bindparams(sa.bindparam("tid", type_=postgresql.UUID(as_uuid=False))),
        {"tid": tenant_id_str},
    ).scalar()

    if existing is None:
        conn.execute(
            sa.text(
                "INSERT INTO permisos (id, tenant_id, codigo, nombre, modulo, descripcion, "
                "created_at, updated_at) "
                "VALUES (gen_random_uuid(), :tid, 'padron:cargar', "
                "'Cargar padrón de alumnos (C-09)', 'padron', "
                "'Importar y gestionar el padrón de alumnos de una materia', NOW(), NOW())"
            ).bindparams(sa.bindparam("tid", type_=postgresql.UUID(as_uuid=False))),
            {"tid": tenant_id_str},
        )

    # PROFESOR: padron:cargar con es_propio=true
    conn.execute(
        sa.text(
            "INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, es_propio, "
            "created_at, updated_at) "
            "SELECT gen_random_uuid(), r.tenant_id, r.id, p.id, true, NOW(), NOW() "
            "FROM roles r, permisos p "
            "WHERE r.tenant_id = :tid AND r.codigo = 'PROFESOR' "
            "AND p.tenant_id = :tid AND p.codigo = 'padron:cargar' "
            "AND NOT EXISTS ("
            "  SELECT 1 FROM rol_permiso rp2 "
            "  WHERE rp2.rol_id = r.id AND rp2.permiso_id = p.id AND rp2.deleted_at IS NULL"
            ")"
        ).bindparams(sa.bindparam("tid", type_=postgresql.UUID(as_uuid=False))),
        {"tid": tenant_id_str},
    )

    # COORDINADOR: padron:cargar con es_propio=false
    conn.execute(
        sa.text(
            "INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, es_propio, "
            "created_at, updated_at) "
            "SELECT gen_random_uuid(), r.tenant_id, r.id, p.id, false, NOW(), NOW() "
            "FROM roles r, permisos p "
            "WHERE r.tenant_id = :tid AND r.codigo = 'COORDINADOR' "
            "AND p.tenant_id = :tid AND p.codigo = 'padron:cargar' "
            "AND NOT EXISTS ("
            "  SELECT 1 FROM rol_permiso rp2 "
            "  WHERE rp2.rol_id = r.id AND rp2.permiso_id = p.id AND rp2.deleted_at IS NULL"
            ")"
        ).bindparams(sa.bindparam("tid", type_=postgresql.UUID(as_uuid=False))),
        {"tid": tenant_id_str},
    )


def downgrade() -> None:
    op.drop_index("ix_entradas_padron_usuario_id", table_name="entradas_padron")
    op.drop_index("ix_entradas_padron_tenant_id", table_name="entradas_padron")
    op.drop_index("ix_entradas_padron_version_id", table_name="entradas_padron")
    op.drop_table("entradas_padron")

    op.drop_index("ix_versiones_padron_activa", table_name="versiones_padron")
    op.drop_index(
        "ix_versiones_padron_tenant_materia_cohorte", table_name="versiones_padron"
    )
    op.drop_table("versiones_padron")
