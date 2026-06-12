"""Seed de RBAC: documentación del permiso atrasados:ver (C-11).

El permiso `atrasados:ver` ya está presente en la migración 002_create_rbac_tables.py
con la siguiente matriz de asignación por rol:

  TUTOR       → atrasados:ver  (es_propio=False)
  PROFESOR    → atrasados:ver  (es_propio=True)   # scope propio (asignación propia)
  COORDINADOR → atrasados:ver  (es_propio=False)  # puede ver cualquier asignación del tenant
  ADMIN       → atrasados:ver  (es_propio=False)  # puede ver cualquier asignación del tenant

Este módulo se importa como referencia de datos y puede usarse para:
- verificar que el permiso existe en runtime
- re-seedear en entornos de desarrollo

Uso:
    from app.core.seed_rbac import ATRASADOS_VER_PERMISO, ATRASADOS_VER_ROLES
"""

ATRASADOS_VER_PERMISO = {
    "codigo": "atrasados:ver",
    "nombre": "Ver alumnos atrasados",
    "modulo": "atrasados",
    "descripcion": "Detectar y ver alumnos con entregas atrasadas",
}

# (rol_codigo, es_propio) — True significa scope restringido al docente titular
ATRASADOS_VER_ROLES: list[tuple[str, bool]] = [
    ("TUTOR", False),
    ("PROFESOR", True),
    ("COORDINADOR", False),
    ("ADMIN", False),
]

# C-20: permisos de perfil y mensajería interna
PERFIL_EDITAR_PERMISO = {
    "codigo": "perfil:editar",
    "nombre": "Editar perfil propio",
    "modulo": "perfil",
    "descripcion": "Editar los datos personales del perfil propio",
}

MENSAJERIA_LEER_PERMISO = {
    "codigo": "mensajeria:leer",
    "nombre": "Leer mensajes",
    "modulo": "mensajeria",
    "descripcion": "Ver inbox y leer threads de mensajería interna",
}

MENSAJERIA_RESPONDER_PERMISO = {
    "codigo": "mensajeria:responder",
    "nombre": "Responder mensajes",
    "modulo": "mensajeria",
    "descripcion": "Responder en threads de mensajería interna",
}

# Todos los roles autenticados tienen acceso a perfil y mensajería
C20_PERMISOS_ROLES: list[tuple[str, bool]] = [
    ("TUTOR", False),
    ("PROFESOR", False),
    ("COORDINADOR", False),
    ("ADMIN", False),
    ("ALUMNO", False),
    ("NEXO", False),
    ("FINANZAS", False),
]
