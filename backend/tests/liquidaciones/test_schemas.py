"""Tests de schemas Pydantic v2 del módulo liquidaciones (C-18).

Verifica: extra='forbid', validadores custom, CerrarLiquidacionRequest.
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError


def test_salario_base_create_extra_forbidden():
    """extra='forbid' rechaza campos no declarados."""
    from app.modules.liquidaciones.schemas.salario_base import SalarioBaseCreate

    with pytest.raises(ValidationError):
        SalarioBaseCreate(
            rol="PROFESOR",
            monto=Decimal("100000"),
            desde="2026-01-01",
            campo_extra="no_deberia_existir",
        )


def test_salario_base_create_monto_negativo():
    """monto negativo → ValidationError."""
    from app.modules.liquidaciones.schemas.salario_base import SalarioBaseCreate

    with pytest.raises(ValidationError):
        SalarioBaseCreate(rol="PROFESOR", monto=Decimal("-1"), desde="2026-01-01")


def test_salario_plus_tope_cero_rechazado():
    """tope_acumulacion=0 → ValidationError."""
    from app.modules.liquidaciones.schemas.salario_plus import SalarioPlusCreate

    with pytest.raises(ValidationError):
        SalarioPlusCreate(
            grupo="PROG", rol="PROFESOR",
            monto=Decimal("15000"),
            desde="2026-01-01",
            tope_acumulacion=Decimal("0"),
        )


def test_salario_plus_tope_negativo_rechazado():
    """tope_acumulacion=-1 → ValidationError."""
    from app.modules.liquidaciones.schemas.salario_plus import SalarioPlusCreate

    with pytest.raises(ValidationError):
        SalarioPlusCreate(
            grupo="PROG", rol="PROFESOR",
            monto=Decimal("15000"),
            desde="2026-01-01",
            tope_acumulacion=Decimal("-1"),
        )


def test_salario_plus_tope_null_valido():
    """tope_acumulacion=None → OK (sin tope)."""
    from app.modules.liquidaciones.schemas.salario_plus import SalarioPlusCreate

    schema = SalarioPlusCreate(
        grupo="PROG", rol="PROFESOR",
        monto=Decimal("15000"),
        desde="2026-01-01",
        tope_acumulacion=None,
    )
    assert schema.tope_acumulacion is None


def test_cerrar_liquidacion_request_confirmar_false():
    """confirmar_cierre=False → ValidationError."""
    from app.modules.liquidaciones.schemas.liquidacion import CerrarLiquidacionRequest

    with pytest.raises(ValidationError):
        CerrarLiquidacionRequest(confirmar_cierre=False, periodo="2026-03")


def test_cerrar_liquidacion_request_valido():
    """confirmar_cierre=True → OK."""
    from app.modules.liquidaciones.schemas.liquidacion import CerrarLiquidacionRequest

    req = CerrarLiquidacionRequest(confirmar_cierre=True, periodo="2026-03")
    assert req.confirmar_cierre is True
    assert req.periodo == "2026-03"


def test_factura_create_extra_forbidden():
    """extra='forbid' en FacturaCreate."""
    from app.modules.liquidaciones.schemas.factura import FacturaCreate
    from uuid import uuid4

    with pytest.raises(ValidationError):
        FacturaCreate(
            usuario_id=uuid4(),
            periodo="2026-03",
            referencia_archivo="local://test",
            campo_invalido="x",
        )
