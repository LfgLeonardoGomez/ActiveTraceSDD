"""Segmentador de filas de liquidación en tres segmentos contables (C-18).

Tres segmentos (F10.6, RN-36, RN-38):
1. general: roles PROFESOR/TUTOR/COORDINADOR no facturantes.
2. nexo: rol NEXO no facturante (aparece separado pero suma al total_sin_factura).
3. facturantes: docentes con excluido_por_factura=True (informativo, no suma).

Función pura — sin efectos secundarios, sin DB.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Protocol, runtime_checkable


@runtime_checkable
class FilaLiquidacionProtocol(Protocol):
    """Protocolo mínimo que una fila de liquidación debe implementar."""

    usuario_id: object
    rol: str
    total: Decimal
    es_nexo: bool
    excluido_por_factura: bool


@dataclass
class SegmentosResult:
    """Resultado del segmentador."""

    general: list = field(default_factory=list)
    nexo: list = field(default_factory=list)
    facturantes: list = field(default_factory=list)
    total_sin_factura: Decimal = Decimal("0")
    total_con_factura: Decimal = Decimal("0")


def segmentar(filas: list) -> SegmentosResult:
    """Segmenta filas de liquidación en tres segmentos contables.

    Reglas de segmentación:
    - Si excluido_por_factura=True → segmento facturantes (no suma a total_sin_factura).
    - Si es_nexo=True y excluido_por_factura=False → segmento nexo (suma a total_sin_factura).
    - En cualquier otro caso → segmento general (suma a total_sin_factura).

    Args:
        filas: Lista de filas con atributos usuario_id, rol, total,
               es_nexo, excluido_por_factura.

    Returns:
        SegmentosResult con los tres segmentos y los KPIs totales.
    """
    resultado = SegmentosResult()

    for fila in filas:
        if fila.excluido_por_factura:
            resultado.facturantes.append(fila)
            resultado.total_con_factura += fila.total
        elif fila.es_nexo:
            resultado.nexo.append(fila)
            resultado.total_sin_factura += fila.total
        else:
            resultado.general.append(fila)
            resultado.total_sin_factura += fila.total

    return resultado
