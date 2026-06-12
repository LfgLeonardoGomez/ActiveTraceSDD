"""Enums del módulo liquidaciones (C-18).

RolDocente: roles de docentes sujetos a liquidación.
EstadoLiquidacion: estados del cierre de un período (Abierta → Cerrada).
EstadoFactura: estados de una factura docente (Pendiente → Abonada).
"""

from enum import StrEnum


class RolDocente(StrEnum):
    """Roles docentes que generan honorarios."""

    PROFESOR = "PROFESOR"
    TUTOR = "TUTOR"
    COORDINADOR = "COORDINADOR"
    NEXO = "NEXO"


class EstadoLiquidacion(StrEnum):
    """Estado de una fila de liquidación.

    Abierta: cálculo on-demand; se puede recalcular.
    Cerrada: montos congelados; inmutable desde repository (D3).
    """

    ABIERTA = "Abierta"
    CERRADA = "Cerrada"


class EstadoFactura(StrEnum):
    """Estado de una factura docente.

    Solo dos estados válidos (RN-39): Pendiente → Abonada.
    La cancelación se gestiona con soft delete, no con un estado.
    """

    PENDIENTE = "Pendiente"
    ABONADA = "Abonada"
