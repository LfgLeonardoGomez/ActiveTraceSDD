"""Códigos de auditoría del módulo liquidaciones (C-18).

Amplía AuditAction del catálogo central. Cada operación significativa
sobre entidades de liquidaciones, grilla salarial y facturas genera
una entrada en el audit log con estos códigos.
"""

from enum import StrEnum


class LiquidacionesAuditAction(StrEnum):
    """Códigos de acción específicos del módulo liquidaciones."""

    # Liquidaciones
    LIQUIDACION_CALCULAR = "LIQUIDACION_CALCULAR"
    LIQUIDACION_CERRAR = "LIQUIDACION_CERRAR"

    # Grilla salarial — SalarioBase
    SALARIO_BASE_CREAR = "SALARIO_BASE_CREAR"
    SALARIO_BASE_MODIFICAR = "SALARIO_BASE_MODIFICAR"
    SALARIO_BASE_ELIMINAR = "SALARIO_BASE_ELIMINAR"

    # Grilla salarial — SalarioPlus
    SALARIO_PLUS_CREAR = "SALARIO_PLUS_CREAR"
    SALARIO_PLUS_MODIFICAR = "SALARIO_PLUS_MODIFICAR"
    SALARIO_PLUS_ELIMINAR = "SALARIO_PLUS_ELIMINAR"

    # Mapeo materia → grupo de plus
    MATERIA_GRUPO_PLUS_CREAR = "MATERIA_GRUPO_PLUS_CREAR"
    MATERIA_GRUPO_PLUS_MODIFICAR = "MATERIA_GRUPO_PLUS_MODIFICAR"
    MATERIA_GRUPO_PLUS_ELIMINAR = "MATERIA_GRUPO_PLUS_ELIMINAR"

    # Facturas
    FACTURA_CARGAR = "FACTURA_CARGAR"
    FACTURA_ABONAR = "FACTURA_ABONAR"
    FACTURA_DELETE = "FACTURA_DELETE"
