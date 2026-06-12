"""Catálogo de permisos del módulo liquidaciones (C-18, decisión D8).

FINANZAS recibe todos; ADMIN recibe solo los :ver.
"""

LIQUIDACIONES_PERMISSIONS = [
    {
        "codigo": "liquidaciones:calcular",
        "nombre": "Calcular liquidación del período",
        "modulo": "liquidaciones",
        "descripcion": "Disparar el cálculo de honorarios de un período",
    },
    {
        "codigo": "liquidaciones:ver",
        "nombre": "Ver liquidación",
        "modulo": "liquidaciones",
        "descripcion": "Ver liquidación actual o histórica del tenant",
    },
    {
        "codigo": "liquidaciones:exportar",
        "nombre": "Exportar liquidación",
        "modulo": "liquidaciones",
        "descripcion": "Obtener la respuesta serializada para exportación externa",
    },
    {
        "codigo": "liquidaciones:cerrar",
        "nombre": "Cerrar liquidación",
        "modulo": "liquidaciones",
        "descripcion": "Ejecutar el cierre inmutable de un período",
    },
    {
        "codigo": "liquidaciones:configurar-salarios",
        "nombre": "Configurar grilla salarial",
        "modulo": "liquidaciones",
        "descripcion": "Modificar SalarioBase, SalarioPlus y MateriaGrupoPlus",
    },
    {
        "codigo": "facturas:cargar",
        "nombre": "Cargar factura docente",
        "modulo": "facturas",
        "descripcion": "Crear nueva factura de docente facturante",
    },
    {
        "codigo": "facturas:ver",
        "nombre": "Ver facturas docentes",
        "modulo": "facturas",
        "descripcion": "Listar y obtener detalle de facturas",
    },
    {
        "codigo": "facturas:abonar",
        "nombre": "Abonar factura docente",
        "modulo": "facturas",
        "descripcion": "Transición Pendiente → Abonada",
    },
]

# (permiso_codigo, rol_codigo, es_propio)
LIQUIDACIONES_ROLE_ASSIGNMENTS: list[tuple[str, str, bool]] = [
    # FINANZAS recibe todos los permisos
    ("liquidaciones:calcular", "FINANZAS", False),
    ("liquidaciones:ver", "FINANZAS", False),
    ("liquidaciones:exportar", "FINANZAS", False),
    ("liquidaciones:cerrar", "FINANZAS", False),
    ("liquidaciones:configurar-salarios", "FINANZAS", False),
    ("facturas:cargar", "FINANZAS", False),
    ("facturas:ver", "FINANZAS", False),
    ("facturas:abonar", "FINANZAS", False),
    # ADMIN solo lectura
    ("liquidaciones:ver", "ADMIN", False),
    ("facturas:ver", "ADMIN", False),
]
