"""002_create_rbac_tables

C-04: RBAC con permisos finos.

Schema changes:
- roles: +codigo (VARCHAR 50, unique por tenant)
- permisos: +codigo (VARCHAR 50, unique por tenant)
- rol_permiso: nueva tabla de unión con es_propio

Data seed:
- 7 roles del dominio vinculados al primer tenant existente
- permisos base derivados de 03_actores_y_roles.md §3.3
- matriz rol_permiso con flag es_propio
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_rbac"
down_revision: Union[str, Sequence[str], None] = "3a51a71a68ef"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Aplica cambios de schema y seed de RBAC."""
    # ------------------------------------------------------------------
    # 1. Schema: agregar codigo a roles y permisos (nullable primero)
    # ------------------------------------------------------------------
    op.add_column("roles", sa.Column("codigo", sa.String(50), nullable=True))
    op.add_column("permisos", sa.Column("codigo", sa.String(50), nullable=True))

    # ------------------------------------------------------------------
    # 2. Schema: crear tabla rol_permiso
    # ------------------------------------------------------------------
    op.create_table(
        "rol_permiso",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "rol_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "permiso_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("permisos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("es_propio", sa.Boolean(), nullable=False, server_default=sa.text("false")),
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

    # ------------------------------------------------------------------
    # 3. Schema: índices únicos parciales (tenant_id, codigo) sin soft-deleted
    # ------------------------------------------------------------------
    op.create_index(
        "idx_roles_tenant_codigo",
        "roles",
        ["tenant_id", "codigo"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_permisos_tenant_codigo",
        "permisos",
        ["tenant_id", "codigo"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ------------------------------------------------------------------
    # 4. Data seed: obtener primer tenant existente
    # ------------------------------------------------------------------
    conn = op.get_bind()
    tenant_id = conn.execute(
        sa.text(
            "SELECT id FROM tenants ORDER BY created_at LIMIT 1"
        )
    ).scalar()

    if tenant_id is None:
        # En un entorno sin tenants, no se puede seedear; dejamos tablas vacías.
        # El provisioning de tenants (post-MVP) deberá seedear roles base.
        return

    tenant_id_str = str(tenant_id)

    # ------------------------------------------------------------------
    # 5. Data seed: insertar roles del dominio
    # ------------------------------------------------------------------
    roles_data = [
        ("ALUMNO", "Alumno", "Estudiante que cursa materias"),
        ("TUTOR", "Tutor", "Auxiliar / ayudante de cátedra"),
        ("PROFESOR", "Profesor", "Docente a cargo de una o más comisiones"),
        ("COORDINADOR", "Coordinador", "Responsable de un conjunto de materias o cohorte"),
        ("NEXO", "Nexo", "Rol de articulación / enlace transversal"),
        ("ADMIN", "Administrador", "Administrador del sistema dentro del tenant"),
        ("FINANZAS", "Finanzas", "Responsable de liquidaciones y honorarios"),
    ]

    for codigo, nombre, descripcion in roles_data:
        op.execute(
            f"INSERT INTO roles (id, tenant_id, codigo, nombre, descripcion, created_at, updated_at) "
            f"VALUES (gen_random_uuid(), '{tenant_id_str}'::uuid, '{codigo}', '{nombre}', '{descripcion}', NOW(), NOW())"
        )

    # ------------------------------------------------------------------
    # 6. Data seed: insertar permisos base
    # ------------------------------------------------------------------
    permisos_data = [
        ("estado_academico:ver", "Ver estado académico propio", "estado_academico", "Consultar el estado académico del usuario"),
        ("evaluacion:reservar", "Reservar instancia de evaluación", "evaluacion", "Reservar instancias de evaluación"),
        ("avisos:confirmar", "Confirmar avisos", "avisos", "Confirmar lectura de avisos"),
        ("calificaciones:importar", "Importar calificaciones", "calificaciones", "Importar calificaciones de comisiones"),
        ("atrasados:ver", "Ver alumnos atrasados", "atrasados", "Detectar y ver alumnos con entregas atrasadas"),
        ("entregas:detectar", "Detectar entregas sin corregir", "entregas", "Detectar entregas pendientes de corrección"),
        ("comunicacion:enviar", "Enviar comunicaciones a alumnos", "comunicacion", "Enviar comunicaciones a alumnos"),
        ("comunicacion:aprobar", "Aprobar comunicaciones masivas", "comunicacion", "Aprobar envío masivo de comunicaciones"),
        ("encuentros:gestionar", "Gestionar encuentros", "encuentros", "Gestionar encuentros de comisiones"),
        ("guardias:registrar", "Registrar guardias", "guardias", "Registrar guardias de docentes"),
        ("tareas:gestionar", "Gestionar tareas internas", "tareas", "Gestionar tareas internas de equipos"),
        ("avisos:publicar", "Publicar avisos", "avisos", "Publicar avisos generales"),
        ("equipos:asignar", "Gestionar equipos docentes", "equipos", "Asignar y gestionar equipos docentes"),
        ("estructura_academica:gestionar", "Gestionar estructura académica", "estructura_academica", "Gestionar carreras, cohortes y materias"),
        ("usuarios:gestionar", "Gestionar usuarios del tenant", "usuarios", "Gestionar usuarios del tenant"),
        ("auditoria:ver", "Ver auditoría", "auditoria", "Ver registros de auditoría"),
        ("grilla_salarial:operar", "Operar grilla salarial", "grilla_salarial", "Operar la grilla salarial"),
        ("liquidaciones:cerrar", "Calcular y cerrar liquidaciones", "liquidaciones", "Calcular y cerrar liquidaciones de honorarios"),
        ("facturas:gestionar", "Gestionar facturas", "facturas", "Gestionar facturas de liquidaciones"),
        ("tenant:configurar", "Configurar el tenant", "tenant", "Configurar parámetros del tenant"),
        ("roles:gestionar", "Gestionar roles", "roles", "Crear, editar y eliminar roles del tenant"),
        ("permisos:gestionar", "Gestionar permisos", "permisos", "Crear, editar y eliminar permisos del tenant"),
    ]

    for codigo, nombre, modulo, descripcion in permisos_data:
        op.execute(
            f"INSERT INTO permisos (id, tenant_id, codigo, nombre, modulo, descripcion, created_at, updated_at) "
            f"VALUES (gen_random_uuid(), '{tenant_id_str}'::uuid, '{codigo}', '{nombre}', '{modulo}', '{descripcion}', NOW(), NOW())"
        )

    # ------------------------------------------------------------------
    # 7. Data seed: matriz rol_permiso
    # ------------------------------------------------------------------
    # Mapeo de rol_codigo -> [(permiso_codigo, es_propio), ...]
    matriz = {
        "ALUMNO": [
            ("estado_academico:ver", True),
            ("evaluacion:reservar", False),
            ("avisos:confirmar", False),
        ],
        "TUTOR": [
            ("avisos:confirmar", False),
            ("atrasados:ver", False),
            ("entregas:detectar", False),
            ("encuentros:gestionar", False),
            ("guardias:registrar", True),
        ],
        "PROFESOR": [
            ("avisos:confirmar", False),
            ("calificaciones:importar", True),
            ("atrasados:ver", True),
            ("entregas:detectar", True),
            ("comunicacion:enviar", True),
            ("encuentros:gestionar", True),
            ("guardias:registrar", True),
            ("tareas:gestionar", True),
        ],
        "COORDINADOR": [
            ("avisos:confirmar", False),
            ("calificaciones:importar", False),
            ("atrasados:ver", False),
            ("entregas:detectar", False),
            ("comunicacion:enviar", False),
            ("comunicacion:aprobar", False),
            ("encuentros:gestionar", False),
            ("guardias:registrar", False),
            ("tareas:gestionar", False),
            ("avisos:publicar", False),
            ("equipos:asignar", False),
            ("auditoria:ver", True),
        ],
        "ADMIN": [
            ("avisos:confirmar", False),
            ("calificaciones:importar", False),
            ("atrasados:ver", False),
            ("entregas:detectar", False),
            ("comunicacion:enviar", False),
            ("comunicacion:aprobar", False),
            ("encuentros:gestionar", False),
            ("guardias:registrar", False),
            ("tareas:gestionar", False),
            ("avisos:publicar", False),
            ("equipos:asignar", False),
            ("estructura_academica:gestionar", False),
            ("usuarios:gestionar", False),
            ("auditoria:ver", False),
            ("tenant:configurar", False),
            ("roles:gestionar", False),
            ("permisos:gestionar", False),
        ],
        "FINANZAS": [
            ("avisos:confirmar", False),
            ("auditoria:ver", False),
            ("grilla_salarial:operar", False),
            ("liquidaciones:cerrar", False),
            ("facturas:gestionar", False),
        ],
        "NEXO": [],
    }

    for rol_codigo, permisos_list in matriz.items():
        for permiso_codigo, es_propio in permisos_list:
            es_propio_str = "true" if es_propio else "false"
            op.execute(
                f"INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, es_propio, created_at, updated_at) "
                f"SELECT gen_random_uuid(), '{tenant_id_str}'::uuid, r.id, p.id, {es_propio_str}, NOW(), NOW() "
                f"FROM roles r, permisos p "
                f"WHERE r.tenant_id = '{tenant_id_str}'::uuid AND r.codigo = '{rol_codigo}' "
                f"AND p.tenant_id = '{tenant_id_str}'::uuid AND p.codigo = '{permiso_codigo}'"
            )

    # ------------------------------------------------------------------
    # 8. Schema: hacer codigo NOT NULL ahora que hay datos
    # ------------------------------------------------------------------
    op.alter_column("roles", "codigo", nullable=False)
    op.alter_column("permisos", "codigo", nullable=False)


def downgrade() -> None:
    """Revierte cambios de schema de RBAC."""
    op.drop_index("idx_roles_tenant_codigo", table_name="roles")
    op.drop_index("idx_permisos_tenant_codigo", table_name="permisos")
    op.drop_table("rol_permiso")
    op.drop_column("roles", "codigo")
    op.drop_column("permisos", "codigo")
