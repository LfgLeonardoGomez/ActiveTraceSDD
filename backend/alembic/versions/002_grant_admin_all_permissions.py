"""Grant ADMIN every permission required by the API (002).

The initial seed (001) only granted ADMIN a partial list of permission codes,
while the routers guard endpoints with require_permission() for a wider set
(estructura, coloquios, encuentros, tareas, avisos, guardias, mensajeria,
facturas, ...). The mismatch made the all-powerful ADMIN role receive 403 on
many endpoints.

This migration is additive and idempotent:
  1. ensures every code referenced by require_permission() exists as a Permiso
     for every tenant;
  2. grants the ADMIN role of each tenant every Permiso of that tenant.

It changes no schema, only seed/RBAC data.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_grant_admin_all_permissions"
down_revision: Union[str, Sequence[str], None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Every permission code referenced by require_permission() across the API.
REQUIRED_PERMISSIONS: list[str] = [
    "atrasados:ver",
    "auditoria:ver",
    "avisos:confirmar",
    "avisos:publicar",
    "calificaciones:importar",
    "calificaciones:vaciar",
    "calificaciones:ver",
    "coloquios:gestionar",
    "coloquios:reservar",
    "coloquios:ver",
    "comisiones:read",
    "comunicacion:aprobar",
    "comunicacion:enviar",
    "encuentros:gestionar",
    "equipos:asignar",
    "estructura:gestionar",
    "estructura:ver",
    "facturas:abonar",
    "facturas:cargar",
    "facturas:ver",
    "guardias:registrar",
    "impersonacion:usar",
    "liquidaciones:cerrar",
    "liquidaciones:configurar-salarios",
    "liquidaciones:exportar",
    "liquidaciones:ver",
    "mensajeria:leer",
    "mensajeria:responder",
    "padron:cargar",
    "perfil:editar",
    "permisos:gestionar",
    "roles:gestionar",
    "tareas:gestionar",
    "usuarios:gestionar",
]


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Ensure every required permission exists for every tenant (idempotent).
    for codigo in REQUIRED_PERMISSIONS:
        modulo = codigo.split(":", 1)[0]
        conn.execute(
            sa.text(
                "INSERT INTO permisos "
                "(id, tenant_id, codigo, nombre, modulo, descripcion, created_at, updated_at) "
                "SELECT gen_random_uuid(), t.id, CAST(:codigo AS varchar), CAST(:nombre AS varchar), "
                "CAST(:modulo AS varchar), CAST(:descripcion AS text), NOW(), NOW() "
                "FROM tenants t "
                "WHERE NOT EXISTS ("
                "  SELECT 1 FROM permisos p "
                "  WHERE p.tenant_id = t.id AND p.codigo = CAST(:codigo AS varchar) AND p.deleted_at IS NULL"
                ")"
            ),
            {
                "codigo": codigo,
                "nombre": codigo,
                "modulo": modulo,
                "descripcion": f"Permiso {codigo}",
            },
        )

    # 2. Grant the ADMIN role of each tenant every permission of that tenant.
    conn.execute(
        sa.text(
            "INSERT INTO rol_permiso "
            "(id, tenant_id, rol_id, permiso_id, es_propio, created_at, updated_at) "
            "SELECT gen_random_uuid(), r.tenant_id, r.id, p.id, false, NOW(), NOW() "
            "FROM roles r "
            "JOIN permisos p ON p.tenant_id = r.tenant_id AND p.deleted_at IS NULL "
            "WHERE r.codigo = 'ADMIN' AND r.deleted_at IS NULL "
            "AND NOT EXISTS ("
            "  SELECT 1 FROM rol_permiso rp "
            "  WHERE rp.rol_id = r.id AND rp.permiso_id = p.id AND rp.deleted_at IS NULL"
            ")"
        )
    )


def downgrade() -> None:
    # Additive seed only; nothing schema-level to revert.
    pass
