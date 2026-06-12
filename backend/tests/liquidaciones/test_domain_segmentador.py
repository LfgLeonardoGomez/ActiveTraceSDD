"""Tests unitarios — domain/segmentador.py (C-18).

TDD puro: sin DB, función pura.
Ciclo: RED → GREEN → TRIANGULATE → REFACTOR.
"""

from dataclasses import dataclass, field
from decimal import Decimal

import pytest


@dataclass
class FilaLiquidacion:
    """DTO mínimo para testear el segmentador."""
    usuario_id: str
    rol: str
    total: Decimal
    es_nexo: bool = False
    excluido_por_factura: bool = False


def test_segmentador_solo_general():
    """Solo docentes en relación de dependencia, no facturantes."""
    from app.modules.liquidaciones.domain.segmentador import segmentar

    filas = [
        FilaLiquidacion("u1", "PROFESOR", Decimal("100000")),
        FilaLiquidacion("u2", "TUTOR", Decimal("80000")),
    ]
    resultado = segmentar(filas)

    assert len(resultado.general) == 2
    assert len(resultado.nexo) == 0
    assert len(resultado.facturantes) == 0
    assert resultado.total_sin_factura == Decimal("180000")
    assert resultado.total_con_factura == Decimal("0")


def test_segmentador_nexo_suma_al_general():
    """NEXO aparece separado pero suma a total_sin_factura."""
    from app.modules.liquidaciones.domain.segmentador import segmentar

    filas = [
        FilaLiquidacion("u1", "PROFESOR", Decimal("100000")),
        FilaLiquidacion("u2", "NEXO", Decimal("80000"), es_nexo=True),
    ]
    resultado = segmentar(filas)

    assert len(resultado.general) == 1
    assert len(resultado.nexo) == 1
    assert resultado.total_sin_factura == Decimal("180000")
    assert resultado.total_con_factura == Decimal("0")


def test_segmentador_facturante_excluido_de_total():
    """Facturante aparece en segmento facturantes pero NO suma a total_sin_factura."""
    from app.modules.liquidaciones.domain.segmentador import segmentar

    filas = [
        FilaLiquidacion("u1", "PROFESOR", Decimal("100000")),
        FilaLiquidacion("u2", "TUTOR", Decimal("150000"), excluido_por_factura=True),
    ]
    resultado = segmentar(filas)

    assert len(resultado.general) == 1
    assert len(resultado.facturantes) == 1
    assert resultado.total_sin_factura == Decimal("100000")
    assert resultado.total_con_factura == Decimal("150000")


def test_segmentador_tres_segmentos_completos():
    """Caso completo con los tres segmentos."""
    from app.modules.liquidaciones.domain.segmentador import segmentar

    filas = [
        FilaLiquidacion("u1", "PROFESOR", Decimal("100000")),
        FilaLiquidacion("u2", "TUTOR", Decimal("80000")),
        FilaLiquidacion("u3", "NEXO", Decimal("60000"), es_nexo=True),
        FilaLiquidacion("f1", "PROFESOR", Decimal("200000"), excluido_por_factura=True),
        FilaLiquidacion("f2", "TUTOR", Decimal("150000"), excluido_por_factura=True),
    ]
    resultado = segmentar(filas)

    assert len(resultado.general) == 2
    assert len(resultado.nexo) == 1
    assert len(resultado.facturantes) == 2
    assert resultado.total_sin_factura == Decimal("240000")  # 100000+80000+60000
    assert resultado.total_con_factura == Decimal("350000")  # 200000+150000


def test_segmentador_vacio():
    """Sin filas: todo cero."""
    from app.modules.liquidaciones.domain.segmentador import segmentar

    resultado = segmentar([])
    assert resultado.general == []
    assert resultado.nexo == []
    assert resultado.facturantes == []
    assert resultado.total_sin_factura == Decimal("0")
    assert resultado.total_con_factura == Decimal("0")


def test_segmentador_nexo_facturante_va_a_facturantes():
    """Un NEXO que es también facturante va al segmento facturantes."""
    from app.modules.liquidaciones.domain.segmentador import segmentar

    filas = [
        FilaLiquidacion("u1", "NEXO", Decimal("80000"), es_nexo=True, excluido_por_factura=True),
    ]
    resultado = segmentar(filas)

    assert len(resultado.nexo) == 0
    assert len(resultado.facturantes) == 1
    assert resultado.total_sin_factura == Decimal("0")
    assert resultado.total_con_factura == Decimal("80000")
