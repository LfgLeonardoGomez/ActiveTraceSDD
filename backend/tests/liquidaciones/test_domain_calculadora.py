"""Tests unitarios — domain/calculadora_liquidacion.py (C-18).

TDD puro: sin DB, funciones puras.
Ciclo: RED → GREEN → TRIANGULATE → REFACTOR.
"""

from decimal import Decimal

import pytest


# ---------- 6.1 calcular_total ----------

def test_calcular_total_base_sin_plus():
    """Caso mínimo: solo base, sin plus."""
    from app.modules.liquidaciones.domain.calculadora_liquidacion import calcular_total

    resultado = calcular_total(Decimal("100000"), [])
    assert resultado == Decimal("100000")


def test_calcular_total_base_con_un_plus():
    """Base + un plus acumulado."""
    from app.modules.liquidaciones.domain.calculadora_liquidacion import calcular_total

    resultado = calcular_total(Decimal("100000"), [Decimal("15000")])
    assert resultado == Decimal("115000")


def test_calcular_total_base_con_multiples_plus():
    """Base + varios plus de distintos grupos."""
    from app.modules.liquidaciones.domain.calculadora_liquidacion import calcular_total

    # 2×15000 + 1×8000 = 38000 → total = 138000
    resultado = calcular_total(Decimal("100000"), [Decimal("30000"), Decimal("8000")])
    assert resultado == Decimal("138000")


def test_calcular_total_suma_correcta_decimal():
    """Verifica precisión decimal en la suma."""
    from app.modules.liquidaciones.domain.calculadora_liquidacion import calcular_total

    resultado = calcular_total(Decimal("99999.99"), [Decimal("0.01")])
    assert resultado == Decimal("100000.00")


# ---------- 6.1 aplicar_tope ----------

def test_aplicar_tope_none_retorna_n():
    """Sin tope (NULL): N_efectivo = N_comisiones."""
    from app.modules.liquidaciones.domain.calculadora_liquidacion import aplicar_tope

    assert aplicar_tope(5, None) == 5


def test_aplicar_tope_menor_que_tope():
    """N < tope: N_efectivo = N."""
    from app.modules.liquidaciones.domain.calculadora_liquidacion import aplicar_tope

    assert aplicar_tope(2, Decimal("3")) == 2


def test_aplicar_tope_igual_a_tope():
    """N == tope: N_efectivo = tope."""
    from app.modules.liquidaciones.domain.calculadora_liquidacion import aplicar_tope

    assert aplicar_tope(3, Decimal("3")) == 3


def test_aplicar_tope_mayor_que_tope():
    """N > tope: N_efectivo = tope (se limita)."""
    from app.modules.liquidaciones.domain.calculadora_liquidacion import aplicar_tope

    assert aplicar_tope(5, Decimal("3")) == 3


def test_aplicar_tope_cero_comisiones():
    """N=0: N_efectivo = 0 siempre."""
    from app.modules.liquidaciones.domain.calculadora_liquidacion import aplicar_tope

    assert aplicar_tope(0, None) == 0
    assert aplicar_tope(0, Decimal("3")) == 0


def test_aplicar_tope_tope_uno():
    """Tope=1: máximo 1 comisión acumula plus."""
    from app.modules.liquidaciones.domain.calculadora_liquidacion import aplicar_tope

    assert aplicar_tope(10, Decimal("1")) == 1


def test_aplicar_tope_tope_grande():
    """Tope grande: nunca limita en práctica."""
    from app.modules.liquidaciones.domain.calculadora_liquidacion import aplicar_tope

    assert aplicar_tope(100, Decimal("999")) == 100
