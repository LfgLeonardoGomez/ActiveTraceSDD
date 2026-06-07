"""001_tenant

Crea la tabla raíz `tenants` y seedea un tenant default con slug 'default'.

Convención de naming: NNN_<nombre>.py — una migración por change de schema.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001_tenant"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Crea tabla tenants e inserta tenant default."""
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("activo", sa.Boolean(), nullable=False, default=True),
        sa.Column("configuracion", postgresql.JSONB(), nullable=True),
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
    )

    # Seed: tenant default para que el sistema no arranque vacío
    op.execute(
        "INSERT INTO tenants (id, nombre, slug, activo, configuracion, created_at, updated_at) "
        "VALUES (gen_random_uuid(), 'Default Tenant', 'default', true, null, NOW(), NOW())"
    )


def downgrade() -> None:
    """Elimina tabla tenants."""
    op.execute("DROP TABLE IF EXISTS tenants")
