"""006_usuario_pii_asignacion

C-07: Extensión de modelo Usuario con PII cifrada + tabla Asignacion.

Schema changes:
- usuarios: agrega email_hash, dni, cuil, cbu, alias_cbu, banco, regional,
  legajo_profesional, facturador (TEXT nullable — PII cifrada o datos de perfil)
- usuarios: índice único parcial (tenant_id, email_hash) WHERE deleted_at IS NULL
- asignaciones: nueva tabla (usuario_id, rol, desde, hasta, comisiones ARRAY,
  materia_id, carrera_id, cohorte_id, responsable_id)
- Seed permisos: usuarios:gestionar (ADMIN), equipos:asignar (COORDINADOR, ADMIN)

Data migration:
- Para usuarios existentes: calcula email_hash = HMAC-SHA256(email, ENCRYPTION_KEY)
  y cifra el email con AES-256-GCM (almacena en email_hash y mantiene email como ciphertext)
"""

import hashlib
import hmac
import os
import base64
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006_usuario_pii_asignacion"
down_revision: Union[str, Sequence[str], None] = "005_carrera_cohorte_materia"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _get_encryption_key() -> bytes:
    """Obtiene la clave de cifrado desde variables de entorno."""
    key_str = os.environ.get("ENCRYPTION_KEY", "")
    if not key_str:
        # Intentar cargar desde .env
        try:
            from app.core.config import Settings
            settings = Settings()
            key_str = settings.encryption_key
        except Exception:
            pass
    if not key_str or len(key_str.encode("utf-8")) != 32:
        raise RuntimeError("ENCRYPTION_KEY must be exactly 32 bytes")
    return key_str.encode("utf-8")


def _hash_email(email: str, key: bytes) -> str:
    """Calcula HMAC-SHA256 del email normalizado."""
    normalized = email.strip().lower()
    return hmac.new(key, normalized.encode("utf-8"), hashlib.sha256).hexdigest()


def _encrypt_value(plain_text: str, key: bytes) -> str:
    """Cifra texto plano con AES-256-GCM."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    cipher_bytes = aesgcm.encrypt(nonce, plain_text.encode("utf-8"), None)
    payload = nonce + cipher_bytes
    return base64.b64encode(payload).decode("ascii")


def upgrade() -> None:
    """Extiende usuarios con PII cifrada y crea tabla asignaciones."""

    # ------------------------------------------------------------------
    # 1. Extender tabla usuarios: agregar columnas PII y hash para lookup
    # ------------------------------------------------------------------
    op.add_column("usuarios", sa.Column("email_hash", sa.Text(), nullable=True))
    op.add_column("usuarios", sa.Column("dni", sa.Text(), nullable=True))
    op.add_column("usuarios", sa.Column("cuil", sa.Text(), nullable=True))
    op.add_column("usuarios", sa.Column("cbu", sa.Text(), nullable=True))
    op.add_column("usuarios", sa.Column("alias_cbu", sa.Text(), nullable=True))
    op.add_column("usuarios", sa.Column("banco", sa.Text(), nullable=True))
    op.add_column("usuarios", sa.Column("regional", sa.Text(), nullable=True))
    op.add_column("usuarios", sa.Column("legajo_profesional", sa.Text(), nullable=True))
    op.add_column("usuarios", sa.Column("facturador", sa.Boolean(), nullable=True, server_default="false"))

    # ------------------------------------------------------------------
    # 2. Data migration: calcular email_hash y cifrar email para usuarios existentes
    # ------------------------------------------------------------------
    conn = op.get_bind()
    try:
        enc_key = _get_encryption_key()
        existing_users = conn.execute(
            sa.text("SELECT id, email FROM usuarios WHERE deleted_at IS NULL AND email_hash IS NULL")
        ).fetchall()

        for user_id, email in existing_users:
            if email and not _is_ciphertext(email):
                email_hash = _hash_email(email, enc_key)
                email_ciphertext = _encrypt_value(email, enc_key)
                conn.execute(
                    sa.text(
                        "UPDATE usuarios SET email_hash = :hash, email = :cipher WHERE id = :uid"
                    ),
                    {"hash": email_hash, "cipher": email_ciphertext, "uid": str(user_id)},
                )
    except Exception:
        # Si no hay clave disponible en migración, continuar sin data migration
        # (los usuarios existentes tendrán email_hash NULL hasta que se rellene)
        pass

    # ------------------------------------------------------------------
    # 3. Índice único parcial (tenant_id, email_hash) WHERE deleted_at IS NULL
    # ------------------------------------------------------------------
    op.create_index(
        "idx_usuarios_tenant_email_hash",
        "usuarios",
        ["tenant_id", "email_hash"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ------------------------------------------------------------------
    # 4. Crear tabla asignaciones
    # ------------------------------------------------------------------
    op.create_table(
        "asignaciones",
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
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("rol", sa.Text(), nullable=False),
        sa.Column("desde", sa.Date(), nullable=False),
        sa.Column("hasta", sa.Date(), nullable=True),
        sa.Column(
            "comisiones",
            postgresql.ARRAY(sa.Text()),
            nullable=True,
            server_default="{}",
        ),
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
            "responsable_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
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
    )

    # ------------------------------------------------------------------
    # 5. Índices en asignaciones
    # ------------------------------------------------------------------
    op.create_index("ix_asignaciones_tenant_id", "asignaciones", ["tenant_id"])
    op.create_index("ix_asignaciones_usuario_id", "asignaciones", ["usuario_id"])
    op.create_index("ix_asignaciones_materia_id", "asignaciones", ["materia_id"])
    op.create_index("ix_asignaciones_carrera_id", "asignaciones", ["carrera_id"])
    op.create_index("ix_asignaciones_responsable_id", "asignaciones", ["responsable_id"])

    # ------------------------------------------------------------------
    # 6. Seed permisos: usuarios:gestionar y equipos:asignar
    # ------------------------------------------------------------------
    tenant_id = conn.execute(
        sa.text("SELECT id FROM tenants ORDER BY created_at LIMIT 1")
    ).scalar()

    if tenant_id is None:
        return

    tenant_id_str = str(tenant_id)

    # Permiso usuarios:gestionar
    existing_ug = conn.execute(
        sa.text(
            "SELECT id FROM permisos "
            "WHERE tenant_id = :tid AND codigo = 'usuarios:gestionar' "
            "AND deleted_at IS NULL LIMIT 1"
        ).bindparams(sa.bindparam("tid", type_=sa.dialects.postgresql.UUID(as_uuid=False))),
        {"tid": tenant_id_str},
    ).scalar()

    if existing_ug is None:
        conn.execute(
            sa.text(
                "INSERT INTO permisos (id, tenant_id, codigo, nombre, modulo, descripcion, created_at, updated_at) "
                "VALUES (gen_random_uuid(), :tid, 'usuarios:gestionar', "
                "'Gestionar usuarios (C-07)', 'usuarios', "
                "'Crear, editar, listar y eliminar usuarios del tenant', NOW(), NOW())"
            ).bindparams(sa.bindparam("tid", type_=postgresql.UUID(as_uuid=False))),
            {"tid": tenant_id_str},
        )

    # Asignar usuarios:gestionar a ADMIN
    conn.execute(
        sa.text(
            "INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, es_propio, created_at, updated_at) "
            "SELECT gen_random_uuid(), r.tenant_id, r.id, p.id, false, NOW(), NOW() "
            "FROM roles r, permisos p "
            "WHERE r.tenant_id = :tid AND r.codigo = 'ADMIN' "
            "AND p.tenant_id = :tid AND p.codigo = 'usuarios:gestionar' "
            "AND NOT EXISTS ("
            "  SELECT 1 FROM rol_permiso rp2 "
            "  WHERE rp2.rol_id = r.id AND rp2.permiso_id = p.id AND rp2.deleted_at IS NULL"
            ")"
        ).bindparams(sa.bindparam("tid", type_=postgresql.UUID(as_uuid=False))),
        {"tid": tenant_id_str},
    )

    # Permiso equipos:asignar
    existing_ea = conn.execute(
        sa.text(
            "SELECT id FROM permisos "
            "WHERE tenant_id = :tid AND codigo = 'equipos:asignar' "
            "AND deleted_at IS NULL LIMIT 1"
        ).bindparams(sa.bindparam("tid", type_=postgresql.UUID(as_uuid=False))),
        {"tid": tenant_id_str},
    ).scalar()

    if existing_ea is None:
        conn.execute(
            sa.text(
                "INSERT INTO permisos (id, tenant_id, codigo, nombre, modulo, descripcion, created_at, updated_at) "
                "VALUES (gen_random_uuid(), :tid, 'equipos:asignar', "
                "'Asignar equipos docentes (C-07)', 'equipos', "
                "'Crear, editar y eliminar asignaciones de roles en contexto academico', NOW(), NOW())"
            ).bindparams(sa.bindparam("tid", type_=postgresql.UUID(as_uuid=False))),
            {"tid": tenant_id_str},
        )

    # Asignar equipos:asignar a ADMIN y COORDINADOR
    for rol_codigo in ("ADMIN", "COORDINADOR"):
        conn.execute(
            sa.text(
                "INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, es_propio, created_at, updated_at) "
                "SELECT gen_random_uuid(), r.tenant_id, r.id, p.id, false, NOW(), NOW() "
                "FROM roles r, permisos p "
                "WHERE r.tenant_id = :tid AND r.codigo = :rol "
                "AND p.tenant_id = :tid AND p.codigo = 'equipos:asignar' "
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


def _is_ciphertext(value: str) -> bool:
    """Heurística: el valor es ya un ciphertext base64 (largo > 50 chars y base64 válido)."""
    if len(value) < 50:
        return False
    try:
        decoded = base64.b64decode(value)
        return len(decoded) >= 28  # nonce(12) + tag(16) mínimo
    except Exception:
        return False


def downgrade() -> None:
    """Revierte la migración 006: elimina tabla asignaciones y columnas PII de usuarios."""

    # Eliminar índices de asignaciones
    op.drop_index("ix_asignaciones_responsable_id", table_name="asignaciones")
    op.drop_index("ix_asignaciones_carrera_id", table_name="asignaciones")
    op.drop_index("ix_asignaciones_materia_id", table_name="asignaciones")
    op.drop_index("ix_asignaciones_usuario_id", table_name="asignaciones")
    op.drop_index("ix_asignaciones_tenant_id", table_name="asignaciones")

    # Eliminar tabla asignaciones
    op.drop_table("asignaciones")

    # Eliminar índice de usuarios
    op.drop_index("idx_usuarios_tenant_email_hash", table_name="usuarios")

    # Eliminar columnas PII de usuarios
    op.drop_column("usuarios", "facturador")
    op.drop_column("usuarios", "legajo_profesional")
    op.drop_column("usuarios", "regional")
    op.drop_column("usuarios", "banco")
    op.drop_column("usuarios", "alias_cbu")
    op.drop_column("usuarios", "cbu")
    op.drop_column("usuarios", "cuil")
    op.drop_column("usuarios", "dni")
    op.drop_column("usuarios", "email_hash")
