"""initial_schema

Schema completo de activia-trace generado desde modelos SQLAlchemy.
Incluye seed de tenant default, roles, permisos y usuario admin.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ================================================================
    # 1. Tablas globales (sin FK)
    # ================================================================
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("configuracion", postgresql.JSONB(), nullable=True),
        sa.Column(
            "requiere_aprobacion_comunicaciones",
            sa.Boolean(),
            nullable=False,
            server_default="false",
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
    )

    op.create_table(
        "rate_limit_buckets",
        sa.Column("resource", sa.String(255), nullable=False, primary_key=True),
        sa.Column(
            "window_start",
            sa.DateTime(timezone=True),
            nullable=False,
            primary_key=True,
        ),
        sa.Column("count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # ================================================================
    # 2. Tablas que dependen solo de tenants
    # ================================================================
    op.create_table(
        "carreras",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("codigo", sa.Text(), nullable=False),
        sa.Column("nombre", sa.Text(), nullable=False),
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default="Activa",
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
        sa.Index(
            "idx_carreras_tenant_codigo",
            "tenant_id",
            "codigo",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
    )

    op.create_table(
        "cohortes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
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
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default="Activa",
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
        sa.Index(
            "idx_cohortes_tenant_carrera_nombre",
            "tenant_id",
            "carrera_id",
            "nombre",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
    )

    op.create_table(
        "materias",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("codigo", sa.Text(), nullable=False),
        sa.Column("nombre", sa.Text(), nullable=False),
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default="Activa",
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
        sa.Index(
            "idx_materias_tenant_codigo",
            "tenant_id",
            "codigo",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
    )

    # ================================================================
    # 3. Usuarios (depende de tenants)
    # ================================================================
    op.create_table(
        "usuarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("apellidos", sa.String(100), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("email_hash", sa.String(64), nullable=True),
        sa.Column("legajo", sa.String(50), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column(
            "is_2fa_enabled",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column("dni", sa.Text(), nullable=True),
        sa.Column("cuil", sa.Text(), nullable=True),
        sa.Column("cbu", sa.Text(), nullable=True),
        sa.Column("alias_cbu", sa.Text(), nullable=True),
        sa.Column("banco", sa.String(100), nullable=True),
        sa.Column("regional", sa.String(100), nullable=True),
        sa.Column("legajo_profesional", sa.String(50), nullable=True),
        sa.Column("facturador", sa.Boolean(), nullable=True),
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
        sa.Index(
            "idx_usuarios_tenant_email_hash",
            "tenant_id",
            "email_hash",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
    )

    # ================================================================
    # 4. Roles y Permisos (dependen de tenants)
    # ================================================================
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("codigo", sa.String(50), nullable=False),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
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
        sa.Index(
            "idx_roles_tenant_codigo",
            "tenant_id",
            "codigo",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
    )

    op.create_table(
        "permisos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("codigo", sa.String(50), nullable=False),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("modulo", sa.String(50), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
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
        sa.Index(
            "idx_permisos_tenant_codigo",
            "tenant_id",
            "codigo",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
    )

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
        sa.Column(
            "es_propio",
            sa.Boolean(),
            nullable=False,
            server_default="false",
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

    # ================================================================
    # 5. Asignaciones (depende de usuarios, materias, carreras, cohortes)
    # ================================================================
    op.create_table(
        "asignaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("rol", sa.Text(), nullable=False),
        sa.Column("desde", sa.Date(), nullable=False),
        sa.Column("hasta", sa.Date(), nullable=True),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materias.id", ondelete="SET NULL"),
            nullable=True,
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
        sa.Column(
            "comisiones",
            postgresql.ARRAY(sa.Text()),
            nullable=True,
            server_default="{}",
        ),
        sa.Column(
            "responsable_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
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
        sa.Index("ix_asignaciones_tenant_id", "tenant_id"),
        sa.Index("ix_asignaciones_usuario_id", "usuario_id"),
        sa.Index("ix_asignaciones_materia_id", "materia_id"),
        sa.Index("ix_asignaciones_carrera_id", "carrera_id"),
        sa.Index("ix_asignaciones_responsable_id", "responsable_id"),
    )

    # ================================================================
    # 6. Tablas auxiliares de usuarios
    # ================================================================
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
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

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
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

    op.create_table(
        "two_factor_enrollments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("encrypted_secret", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("backup_code_hashes", postgresql.JSONB(), nullable=True),
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

    # ================================================================
    # 7. Audit Log (append-only)
    # ================================================================
    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "fecha_hora",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "impersonado_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("materia_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("accion", sa.String(100), nullable=False),
        sa.Column("detalle", postgresql.JSONB(), nullable=True),
        sa.Column("filas_afectadas", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ip", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
    )
    op.create_index("ix_audit_log_tenant_id", "audit_log", ["tenant_id"])

    # ================================================================
    # 8. Padrón (versiones y entradas)
    # ================================================================
    op.create_table(
        "versiones_padron",
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
            server_default=sa.func.now(),
        ),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "origen",
            sa.String(20),
            nullable=False,
            server_default="manual",
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
        sa.Index(
            "ix_versiones_padron_tenant_materia_cohorte",
            "tenant_id",
            "materia_id",
            "cohorte_id",
        ),
        sa.Index(
            "ix_versiones_padron_activa",
            "tenant_id",
            "materia_id",
            "cohorte_id",
            "activa",
        ),
    )

    op.create_table(
        "entradas_padron",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
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
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Index("ix_entradas_padron_version_id", "version_id"),
        sa.Index("ix_entradas_padron_tenant_id", "tenant_id"),
        sa.Index("ix_entradas_padron_usuario_id", "usuario_id"),
    )

    # ================================================================
    # 9. Calificaciones y Umbrales
    # ================================================================
    op.create_table(
        "calificaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
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
        sa.Index("ix_calificaciones_tenant_materia", "tenant_id", "materia_id"),
        sa.Index("ix_calificaciones_entrada_padron", "entrada_padron_id"),
        sa.Index(
            "ix_calificaciones_scope",
            "tenant_id",
            "usuario_importador_id",
            "materia_id",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "entrada_padron_id",
            "materia_id",
            "actividad",
            "usuario_importador_id",
            name="uq_calificacion_scope",
        ),
    )

    op.create_table(
        "umbrales_materia",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
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
            postgresql.JSONB(),
            nullable=False,
            server_default='["Satisfactorio", "Supera lo esperado"]',
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
        sa.Index("ix_umbrales_materia_tenant_materia", "tenant_id", "materia_id"),
        sa.Index("ix_umbrales_materia_asignacion", "asignacion_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "asignacion_id",
            "materia_id",
            name="uq_umbral_asignacion_materia",
        ),
    )

    # ================================================================
    # 10. Comunicación
    # ================================================================
    op.create_table(
        "comunicacion",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
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
        sa.Column("materia_id", postgresql.UUID(as_uuid=True), nullable=False),
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
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("aprobado", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("enviado_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ================================================================
    # 11. Evaluaciones y Coloquios
    # ================================================================
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
        sa.Index("ix_evaluacion_tenant", "tenant_id"),
        sa.Index("ix_evaluacion_materia", "tenant_id", "materia_id"),
        sa.Index("ix_evaluacion_cohorte", "tenant_id", "cohorte_id"),
    )

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
        sa.Index("ix_evaluacion_candidato_evaluacion", "evaluacion_id"),
        sa.Index("ix_evaluacion_candidato_alumno", "alumno_id"),
    )

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
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default="Activa",
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
        sa.Index("ix_reserva_evaluacion_evaluacion", "evaluacion_id"),
        sa.Index("ix_reserva_evaluacion_alumno", "alumno_id"),
        sa.Index("ix_reserva_evaluacion_tenant_estado", "tenant_id", "estado"),
    )

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
        sa.UniqueConstraint(
            "evaluacion_id",
            "alumno_id",
            name="uq_resultado_evaluacion",
        ),
        sa.Index("ix_resultado_evaluacion_evaluacion", "evaluacion_id"),
    )

    # ================================================================
    # 12. Avisos y Acknowledgment
    # ================================================================
    op.create_table(
        "aviso",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("alcance", sa.String(30), nullable=False),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materias.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "cohorte_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cohortes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("rol_destino", sa.String(30), nullable=True),
        sa.Column("severidad", sa.String(30), nullable=False),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column("inicio_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fin_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "requiere_ack",
            sa.Boolean(),
            nullable=False,
            server_default="false",
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
        sa.Index("ix_aviso_tenant", "tenant_id"),
        sa.Index(
            "ix_aviso_tenant_activo_vigencia",
            "tenant_id",
            "activo",
            "inicio_en",
            "fin_en",
        ),
        sa.Index(
            "ix_aviso_alcance",
            "tenant_id",
            "alcance",
            "materia_id",
            "cohorte_id",
        ),
    )

    op.create_table(
        "acknowledgment_aviso",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "aviso_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("aviso.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("confirmado_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.UniqueConstraint(
            "aviso_id",
            "usuario_id",
            name="uq_ack_aviso_usuario",
        ),
        sa.Index("ix_ack_aviso_aviso", "aviso_id"),
        sa.Index("ix_ack_aviso_usuario", "usuario_id"),
    )

    # ================================================================
    # 13. Tareas y Comentarios
    # ================================================================
    op.create_table(
        "tarea",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("criterio_cierre", sa.Text(), nullable=True),
        sa.Column(
            "estado",
            sa.String(30),
            nullable=False,
            server_default="Pendiente",
        ),
        sa.Column("aprobada", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("devuelta", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "asignado_a",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "asignado_por",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "revisada_por",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("revisada_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materias.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("contexto_id", postgresql.UUID(as_uuid=True), nullable=True),
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
        sa.Index("ix_tarea_tenant_estado", "tenant_id", "estado"),
        sa.Index("ix_tarea_asignado_estado", "tenant_id", "asignado_a", "estado"),
        sa.Index("ix_tarea_materia", "tenant_id", "materia_id"),
    )

    op.create_table(
        "comentario_tarea",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "tarea_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tarea.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "autor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("contenido", sa.Text(), nullable=False),
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
        sa.Index("ix_comentario_tarea_tarea", "tarea_id"),
    )

    # ================================================================
    # 14. Slots, Instancias y Guardias
    # ================================================================
    op.create_table(
        "slot_encuentros",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
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
        sa.Column("dia_semana", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("hora", sa.String(5), nullable=False),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("cant_semanas", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("meet_url", sa.Text(), nullable=True),
        sa.Column("vigencia", sa.Text(), nullable=True),
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
        sa.Index("ix_slot_encuentros_tenant_id", "tenant_id"),
        sa.Index("ix_slot_encuentros_materia_id", "materia_id"),
        sa.Index("ix_slot_encuentros_carrera_id", "carrera_id"),
        sa.Index("ix_slot_encuentros_cohorte_id", "cohorte_id"),
        sa.Index("ix_slot_encuentros_creador_id", "creador_id"),
    )

    op.create_table(
        "instancias_encuentro",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
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
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Index("ix_instancias_encuentro_tenant_id", "tenant_id"),
        sa.Index("ix_instancias_encuentro_slot_id", "slot_id"),
        sa.Index("ix_instancias_encuentro_materia_id", "materia_id"),
        sa.Index("ix_instancias_encuentro_fecha", "fecha"),
    )

    op.create_table(
        "guardias",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
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
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Index("ix_guardias_tenant_id", "tenant_id"),
        sa.Index("ix_guardias_tutor_id", "tutor_id"),
        sa.Index("ix_guardias_materia_id", "materia_id"),
        sa.Index("ix_guardias_carrera_id", "carrera_id"),
        sa.Index("ix_guardias_cohorte_id", "cohorte_id"),
    )

    # ================================================================
    # 15. Programas y Fechas Académicas
    # ================================================================
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
        sa.Index(
            "idx_programa_materia_combinacion",
            "tenant_id",
            "materia_id",
            "carrera_id",
            "cohorte_id",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
    )

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
        sa.Index("ix_fecha_academica_materia", "tenant_id", "materia_id"),
        sa.Index(
            "ix_fecha_academica_materia_cohorte",
            "tenant_id",
            "materia_id",
            "cohorte_id",
        ),
        sa.Index("ix_fecha_academica_fecha", "tenant_id", "fecha"),
    )

    # ================================================================
    # 16. Mensajes
    # ================================================================
    op.create_table(
        "mensaje",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "remitente_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "destinatario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("asunto", sa.String(500), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column(
            "parent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mensaje.id", ondelete="RESTRICT"),
            nullable=True,
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
        sa.Index(
            "ix_mensaje_tenant_destinatario_parent_deleted",
            "tenant_id",
            "destinatario_id",
            "parent_id",
            "deleted_at",
        ),
        sa.Index(
            "ix_mensaje_tenant_parent_created",
            "tenant_id",
            "parent_id",
            "created_at",
        ),
    )

    # ================================================================
    # SEED DATA
    # ================================================================
    conn = op.get_bind()

    # Tenant default
    conn.execute(
        sa.text(
            "INSERT INTO tenants (id, nombre, slug, activo, created_at, updated_at) "
            "VALUES (gen_random_uuid(), 'Default Tenant', 'default', true, NOW(), NOW())"
        )
    )

    # Obtener tenant_id
    tenant_id = conn.execute(
        sa.text("SELECT id FROM tenants WHERE slug = 'default'")
    ).scalar()
    tid = str(tenant_id)

    # Roles base
    roles_data = [
        ("ADMIN", "Administrador", "Acceso total al sistema"),
        ("COORDINADOR", "Coordinador", "Gestión académica y equipos"),
        ("PROFESOR", "Profesor", "Docente con alumnos a cargo"),
        ("TUTOR", "Tutor", "Acompañamiento y guardias"),
        ("ALUMNO", "Alumno", "Estudiante del programa"),
        ("NEXO", "Nexo", "Vínculo institucional"),
        ("FINANZAS", "Finanzas", "Gestión de liquidaciones"),
    ]
    for codigo, nombre, desc in roles_data:
        conn.execute(
            sa.text(
                "INSERT INTO roles (id, tenant_id, codigo, nombre, descripcion, created_at, updated_at) "
                "VALUES (gen_random_uuid(), :tid, :codigo, :nombre, :desc, NOW(), NOW())"
            ),
            {"tid": tid, "codigo": codigo, "nombre": nombre, "desc": desc},
        )

    # Permisos base
    permisos_data = [
        ("usuarios:gestionar", "Gestionar usuarios", "usuarios", "Crear, editar, listar y eliminar usuarios"),
        ("equipos:asignar", "Asignar equipos docentes", "equipos", "Crear, editar y eliminar asignaciones de roles"),
        ("estructura:ver", "Ver estructura académica", "estructura", "Visualizar programas y fechas académicas"),
        ("alumnos:read", "Ver alumnos", "alumnos", "Listar y ver detalle de alumnos"),
        ("materias:read", "Ver materias", "materias", "Listar y ver detalle de materias"),
        ("comisiones:read", "Ver comisiones", "comisiones", "Listar y ver detalle de comisiones"),
        ("comunicacion:read", "Ver comunicación", "comunicacion", "Listar y ver mensajes/envíos"),
        ("equipos:read", "Ver equipos", "equipos", "Listar equipos docentes"),
        ("equipos:ver", "Ver equipos coordinación", "equipos", "Ver equipos en módulo coordinación"),
        ("liquidaciones:read", "Ver liquidaciones", "liquidaciones", "Listar liquidaciones"),
        ("liquidaciones:ver", "Ver liquidaciones finanzas", "liquidaciones", "Ver liquidaciones en módulo finanzas"),
        ("liquidaciones:configurar-salarios", "Configurar salarios", "liquidaciones", "Configurar tablas salariales"),
        ("facturas:ver", "Ver facturas", "finanzas", "Listar facturas"),
        ("estructura:gestionar", "Gestionar estructura académica", "estructura", "Crear/editar programas y fechas"),
        ("encuentros:ver", "Ver encuentros", "encuentros", "Listar encuentros"),
        ("coloquios:ver", "Ver coloquios", "coloquios", "Listar coloquios"),
        ("tareas:ver", "Ver tareas", "tareas", "Listar tareas"),
        ("avisos:ver", "Ver avisos", "avisos", "Listar avisos"),
        ("monitor:ver", "Ver monitor", "monitor", "Ver dashboard de monitor"),
        ("auditoria:ver", "Ver auditoría", "auditoria", "Listar logs de auditoría"),
    ]
    for codigo, nombre, modulo, desc in permisos_data:
        conn.execute(
            sa.text(
                "INSERT INTO permisos (id, tenant_id, codigo, nombre, modulo, descripcion, created_at, updated_at) "
                "VALUES (gen_random_uuid(), :tid, :codigo, :nombre, :modulo, :desc, NOW(), NOW())"
            ),
            {"tid": tid, "codigo": codigo, "nombre": nombre, "modulo": modulo, "desc": desc},
        )

    # Asignar permisos a roles
    rbac_matrix = [
        # ADMIN: todos los permisos
        ("ADMIN", "usuarios:gestionar"),
        ("ADMIN", "equipos:asignar"),
        ("ADMIN", "estructura:ver"),
        ("ADMIN", "alumnos:read"),
        ("ADMIN", "materias:read"),
        ("ADMIN", "comisiones:read"),
        ("ADMIN", "comunicacion:read"),
        ("ADMIN", "equipos:read"),
        ("ADMIN", "equipos:ver"),
        ("ADMIN", "liquidaciones:read"),
        ("ADMIN", "liquidaciones:ver"),
        ("ADMIN", "liquidaciones:configurar-salarios"),
        ("ADMIN", "facturas:ver"),
        ("ADMIN", "estructura:gestionar"),
        ("ADMIN", "encuentros:ver"),
        ("ADMIN", "coloquios:ver"),
        ("ADMIN", "tareas:ver"),
        ("ADMIN", "avisos:ver"),
        ("ADMIN", "monitor:ver"),
        ("ADMIN", "auditoria:ver"),
        # COFINAZAS (FINANZAS)
        ("FINANZAS", "liquidaciones:ver"),
        ("FINANZAS", "liquidaciones:configurar-salarios"),
        ("FINANZAS", "facturas:ver"),
        ("FINANZAS", "liquidaciones:read"),
        # COORDINADOR
        ("COORDINADOR", "equipos:asignar"),
        ("COORDINADOR", "estructura:ver"),
        ("COORDINADOR", "equipos:ver"),
        ("COORDINADOR", "estructura:gestionar"),
        ("COORDINADOR", "encuentros:ver"),
        ("COORDINADOR", "coloquios:ver"),
        ("COORDINADOR", "tareas:ver"),
        ("COORDINADOR", "avisos:ver"),
        ("COORDINADOR", "monitor:ver"),
        # PROFESOR
        ("PROFESOR", "estructura:ver"),
    ]
    for rol_codigo, permiso_codigo in rbac_matrix:
        conn.execute(
            sa.text(
                "INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, es_propio, created_at, updated_at) "
                "SELECT gen_random_uuid(), :tid, r.id, p.id, false, NOW(), NOW() "
                "FROM roles r, permisos p "
                "WHERE r.tenant_id = :tid AND r.codigo = :rol "
                "AND p.tenant_id = :tid AND p.codigo = :permiso "
                "AND NOT EXISTS ("
                "  SELECT 1 FROM rol_permiso rp2 "
                "  WHERE rp2.rol_id = r.id AND rp2.permiso_id = p.id AND rp2.deleted_at IS NULL"
                ")"
            ),
            {"tid": tid, "rol": rol_codigo, "permiso": permiso_codigo},
        )


def downgrade() -> None:
    # Orden inverso respetando dependencias FK
    op.drop_table("mensaje")
    op.drop_table("fecha_academica")
    op.drop_table("programa_materia")
    op.drop_table("guardias")
    op.drop_table("instancias_encuentro")
    op.drop_table("slot_encuentros")
    op.drop_table("comentario_tarea")
    op.drop_table("tarea")
    op.drop_table("acknowledgment_aviso")
    op.drop_table("aviso")
    op.drop_table("resultado_evaluacion")
    op.drop_table("reserva_evaluacion")
    op.drop_table("evaluacion_candidato")
    op.drop_table("evaluacion")
    op.drop_table("comunicacion")
    op.drop_table("umbrales_materia")
    op.drop_table("calificaciones")
    op.drop_table("entradas_padron")
    op.drop_table("versiones_padron")
    op.drop_table("audit_log")
    op.drop_table("two_factor_enrollments")
    op.drop_table("password_reset_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("asignaciones")
    op.drop_table("rol_permiso")
    op.drop_table("permisos")
    op.drop_table("roles")
    op.drop_table("usuarios")
    op.drop_table("materias")
    op.drop_table("cohortes")
    op.drop_table("carreras")
    op.drop_table("rate_limit_buckets")
    op.drop_table("tenants")
