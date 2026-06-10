"""007_slot_encuentro_instancia_guardia

C-13: Creación de tablas SlotEncuentro, InstanciaEncuentro y Guardia.

Schema changes:
- slot_encuentros: plantilla de recurrencia de encuentros sincrónicos
- instancias_encuentro: encuentros concretos derivados de slot o independientes
- guardias: registro de guardias de atención a alumnos

Seed permisos:
- encuentros:gestionar → PROFESOR, TUTOR, COORDINADOR, ADMIN
- guardias:registrar → TUTOR, PROFESOR, COORDINADOR, ADMIN
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007_slot_encuentro_instancia_guardia"
down_revision: Union[str, Sequence[str], None] = "006_usuario_pii_asignacion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea tablas de encuentros y guardias, e inserta permisos base."""

    # ------------------------------------------------------------------
    # 1. Tabla slot_encuentros
    # ------------------------------------------------------------------
    op.create_table(
        "slot_encuentros",
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
            "creador_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
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
            sa.ForeignKey("carreras.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "cohorte_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cohortes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("titulo", sa.Text(), nullable=False),
        sa.Column("dia_semana", sa.Integer(), nullable=False, default=0),
        sa.Column("hora", sa.String(5), nullable=False),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("cant_semanas", sa.Integer(), nullable=False, default=1),
        sa.Column("meet_url", sa.Text(), nullable=True),
        sa.Column("vigencia", sa.Text(), nullable=True),
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

    # Índices de slot_encuentros
    op.create_index("ix_slot_encuentros_tenant_id", "slot_encuentros", ["tenant_id"])
    op.create_index("ix_slot_encuentros_materia_id", "slot_encuentros", ["materia_id"])
    op.create_index("ix_slot_encuentros_carrera_id", "slot_encuentros", ["carrera_id"])
    op.create_index("ix_slot_encuentros_cohorte_id", "slot_encuentros", ["cohorte_id"])
    op.create_index("ix_slot_encuentros_creador_id", "slot_encuentros", ["creador_id"])

    # ------------------------------------------------------------------
    # 2. Tabla instancias_encuentro
    # ------------------------------------------------------------------
    op.create_table(
        "instancias_encuentro",
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
            "slot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("slot_encuentros.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materias.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("titulo", sa.Text(), nullable=True),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("hora", sa.String(5), nullable=False),
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default="Programado",
        ),
        sa.Column("meet_url", sa.Text(), nullable=True),
        sa.Column("video_url", sa.Text(), nullable=True),
        sa.Column("comentario", sa.Text(), nullable=True),
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

    # Índices de instancias_encuentro
    op.create_index("ix_instancias_encuentro_tenant_id", "instancias_encuentro", ["tenant_id"])
    op.create_index("ix_instancias_encuentro_slot_id", "instancias_encuentro", ["slot_id"])
    op.create_index("ix_instancias_encuentro_materia_id", "instancias_encuentro", ["materia_id"])
    op.create_index("ix_instancias_encuentro_fecha", "instancias_encuentro", ["fecha"])

    # ------------------------------------------------------------------
    # 3. Tabla guardias
    # ------------------------------------------------------------------
    op.create_table(
        "guardias",
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
            "tutor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
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
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("horario", sa.String(11), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default="Pendiente",
        ),
        sa.Column("comentarios", sa.Text(), nullable=True),
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

    # Índices de guardias
    op.create_index("ix_guardias_tenant_id", "guardias", ["tenant_id"])
    op.create_index("ix_guardias_tutor_id", "guardias", ["tutor_id"])
    op.create_index("ix_guardias_materia_id", "guardias", ["materia_id"])
    op.create_index("ix_guardias_carrera_id", "guardias", ["carrera_id"])
    op.create_index("ix_guardias_cohorte_id", "guardias", ["cohorte_id"])

    # ------------------------------------------------------------------
    # 4. Seed permisos: encuentros:gestionar y guardias:registrar
    # ------------------------------------------------------------------
    conn = op.get_bind()

    tenant_id = conn.execute(
        sa.text("SELECT id FROM tenants ORDER BY created_at LIMIT 1")
    ).scalar()

    if tenant_id is None:
        return

    tenant_id_str = str(tenant_id)

    # Permiso encuentros:gestionar
    existing_eg = conn.execute(
        sa.text(
            "SELECT id FROM permisos "
            "WHERE tenant_id = :tid AND codigo = 'encuentros:gestionar' "
            "AND deleted_at IS NULL LIMIT 1"
        ).bindparams(sa.bindparam("tid", type_=sa.dialects.postgresql.UUID(as_uuid=False))),
        {"tid": tenant_id_str},
    ).scalar()

    if existing_eg is None:
        conn.execute(
            sa.text(
                "INSERT INTO permisos (id, tenant_id, codigo, nombre, modulo, descripcion, created_at, updated_at) "
                "VALUES (gen_random_uuid(), :tid, 'encuentros:gestionar', "
                "'Gestionar encuentros (C-13)', 'encuentros', "
                "'Crear, editar, listar y eliminar encuentros y slots', NOW(), NOW())"
            ).bindparams(sa.bindparam("tid", type_=postgresql.UUID(as_uuid=False))),
            {"tid": tenant_id_str},
        )

    # Permiso guardias:registrar
    existing_gr = conn.execute(
        sa.text(
            "SELECT id FROM permisos "
            "WHERE tenant_id = :tid AND codigo = 'guardias:registrar' "
            "AND deleted_at IS NULL LIMIT 1"
        ).bindparams(sa.bindparam("tid", type_=sa.dialects.postgresql.UUID(as_uuid=False))),
        {"tid": tenant_id_str},
    ).scalar()

    if existing_gr is None:
        conn.execute(
            sa.text(
                "INSERT INTO permisos (id, tenant_id, codigo, nombre, modulo, descripcion, created_at, updated_at) "
                "VALUES (gen_random_uuid(), :tid, 'guardias:registrar', "
                "'Registrar guardias (C-13)', 'guardias', "
                "'Registrar y listar guardias de atencion a alumnos', NOW(), NOW())"
            ).bindparams(sa.bindparam("tid", type_=postgresql.UUID(as_uuid=False))),
            {"tid": tenant_id_str},
        )

    # Asignar encuentros:gestionar a PROFESOR, TUTOR, COORDINADOR, ADMIN
    for rol_codigo in ("PROFESOR", "TUTOR", "COORDINADOR", "ADMIN"):
        conn.execute(
            sa.text(
                "INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, es_propio, created_at, updated_at) "
                "SELECT gen_random_uuid(), r.tenant_id, r.id, p.id, false, NOW(), NOW() "
                "FROM roles r, permisos p "
                "WHERE r.tenant_id = :tid AND r.codigo = :rol "
                "AND p.tenant_id = :tid AND p.codigo = 'encuentros:gestionar' "
                "AND NOT EXISTS ("
                "  SELECT 1 FROM rol_permiso rp2 "
                "  WHERE rp2.rol_id = r.id AND rp2.permiso_id = p.id AND rp2.deleted_at IS NULL"
                ")"
            ).bindparams(
                sa.bindparam("tid", type_=postgresql.UUID(as_uuid=False)),
                sa.bindparam("rol"),
            ),
            {"tid": tenant_id_str, "rol": rol_codigo},
        )

    # Asignar guardias:registrar a TUTOR, PROFESOR, COORDINADOR, ADMIN
    for rol_codigo in ("TUTOR", "PROFESOR", "COORDINADOR", "ADMIN"):
        conn.execute(
            sa.text(
                "INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, es_propio, created_at, updated_at) "
                "SELECT gen_random_uuid(), r.tenant_id, r.id, p.id, false, NOW(), NOW() "
                "FROM roles r, permisos p "
                "WHERE r.tenant_id = :tid AND r.codigo = :rol "
                "AND p.tenant_id = :tid AND p.codigo = 'guardias:registrar' "
                "AND NOT EXISTS ("
                "  SELECT 1 FROM rol_permiso rp2 "
                "  WHERE rp2.rol_id = r.id AND rp2.permiso_id = p.id AND rp2.deleted_at IS NULL"
                ")"
            ).bindparams(
                sa.bindparam("tid", type_=postgresql.UUID(as_uuid=False)),
                sa.bindparam("rol"),
            ),
            {"tid": tenant_id_str, "rol": rol_codigo},
        )


def downgrade() -> None:
    """Revierte la migración 007: elimina tablas de encuentros y guardias."""

    # Eliminar índices de guardias
    op.drop_index("ix_guardias_cohorte_id", table_name="guardias")
    op.drop_index("ix_guardias_carrera_id", table_name="guardias")
    op.drop_index("ix_guardias_materia_id", table_name="guardias")
    op.drop_index("ix_guardias_tutor_id", table_name="guardias")
    op.drop_index("ix_guardias_tenant_id", table_name="guardias")

    # Eliminar tabla guardias
    op.drop_table("guardias")

    # Eliminar índices de instancias_encuentro
    op.drop_index("ix_instancias_encuentro_fecha", table_name="instancias_encuentro")
    op.drop_index("ix_instancias_encuentro_materia_id", table_name="instancias_encuentro")
    op.drop_index("ix_instancias_encuentro_slot_id", table_name="instancias_encuentro")
    op.drop_index("ix_instancias_encuentro_tenant_id", table_name="instancias_encuentro")

    # Eliminar tabla instancias_encuentro
    op.drop_table("instancias_encuentro")

    # Eliminar índices de slot_encuentros
    op.drop_index("ix_slot_encuentros_creador_id", table_name="slot_encuentros")
    op.drop_index("ix_slot_encuentros_cohorte_id", table_name="slot_encuentros")
    op.drop_index("ix_slot_encuentros_carrera_id", table_name="slot_encuentros")
    op.drop_index("ix_slot_encuentros_materia_id", table_name="slot_encuentros")
    op.drop_index("ix_slot_encuentros_tenant_id", table_name="slot_encuentros")

    # Eliminar tabla slot_encuentros
    op.drop_table("slot_encuentros")

    # Nota: los permisos seedeados quedan como huérfanos; no se eliminan
    # para evitar romper referencias si ya se usaron en producción.
