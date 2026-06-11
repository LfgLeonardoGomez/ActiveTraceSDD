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
