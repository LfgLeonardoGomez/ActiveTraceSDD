"""009_comunicacion

C-12: Tabla comunicacion y flag de aprobación en tenants.

Schema changes:
- comunicacion: tabla de mensajes salientes con ciclo de vida completo
  (Pendiente/Enviando/Enviado/Error/Cancelado). destinatario cifrado AES-256.
- tenants: columna requiere_aprobacion_comunicaciones (bool, default false).
- rol_permiso: agregar comunicacion:enviar al rol TUTOR (faltaba en seed C-04).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "009_comunicacion"
down_revision: Union[str, Sequence[str], None] = "008_calificacion_umbral"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea tabla comunicacion y agrega columna en tenants."""
    # ------------------------------------------------------------------
    # 1. Agregar columna requiere_aprobacion_comunicaciones a tenants
    # ------------------------------------------------------------------
    op.add_column(
        "tenants",
        sa.Column(
            "requiere_aprobacion_comunicaciones",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    # ------------------------------------------------------------------
    # 2. Crear tabla comunicacion
    # ------------------------------------------------------------------
    op.create_table(
        "comunicacion",
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
            "enviado_por",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("destinatario", sa.Text(), nullable=False),
        sa.Column("asunto", sa.String(500), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default="Pendiente",
        ),
        sa.Column(
            "lote_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "aprobado",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "enviado_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("error_detalle", sa.Text(), nullable=True),
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
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # Índices de lookup eficiente
    op.create_index("idx_comunicacion_tenant_id", "comunicacion", ["tenant_id"])
    op.create_index("idx_comunicacion_lote_id", "comunicacion", ["lote_id"])
    op.create_index("idx_comunicacion_estado", "comunicacion", ["estado"])
    op.create_index(
        "idx_comunicacion_tenant_estado",
        "comunicacion",
        ["tenant_id", "estado"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ------------------------------------------------------------------
    # 3. Data fix: agregar comunicacion:enviar a TUTOR si no existe
    # ------------------------------------------------------------------
    conn = op.get_bind()
    tenant_id = conn.execute(
        sa.text("SELECT id FROM tenants ORDER BY created_at LIMIT 1")
    ).scalar()

    if tenant_id is None:
        return

    tenant_id_str = str(tenant_id)

    # Verificar si TUTOR ya tiene comunicacion:enviar
    existing = conn.execute(
        sa.text(
            "SELECT COUNT(*) FROM rol_permiso rp "
            "JOIN roles r ON rp.rol_id = r.id "
            "JOIN permisos p ON rp.permiso_id = p.id "
            f"WHERE r.tenant_id = '{tenant_id_str}'::uuid "
            f"AND r.codigo = 'TUTOR' "
            f"AND p.codigo = 'comunicacion:enviar' "
            "AND rp.deleted_at IS NULL"
        )
    ).scalar()

    if existing == 0:
        op.execute(
            f"INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, es_propio, created_at, updated_at) "
            f"SELECT gen_random_uuid(), '{tenant_id_str}'::uuid, r.id, p.id, false, NOW(), NOW() "
            f"FROM roles r, permisos p "
            f"WHERE r.tenant_id = '{tenant_id_str}'::uuid AND r.codigo = 'TUTOR' "
            f"AND p.tenant_id = '{tenant_id_str}'::uuid AND p.codigo = 'comunicacion:enviar'"
        )


def downgrade() -> None:
    """Revierte cambios de schema."""
    op.drop_index("idx_comunicacion_tenant_estado", table_name="comunicacion")
    op.drop_index("idx_comunicacion_estado", table_name="comunicacion")
    op.drop_index("idx_comunicacion_lote_id", table_name="comunicacion")
    op.drop_index("idx_comunicacion_tenant_id", table_name="comunicacion")
    op.drop_table("comunicacion")
    op.drop_column("tenants", "requiere_aprobacion_comunicaciones")
