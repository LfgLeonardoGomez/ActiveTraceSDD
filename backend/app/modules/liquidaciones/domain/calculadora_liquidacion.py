"""Lógica de cálculo de honorarios — funciones puras (C-18).

calcular_total: suma monto_base + todos los plus acumulados.
aplicar_tope: aplica el tope de acumulación (PA-23, decisión D2).

Algoritmo de acumulación (RN-33 + PA-23):
    para cada (grupo, rol) del docente en el período:
        N_comisiones = count(asignaciones del docente en materias del grupo)
        tope = SalarioPlus.tope_acumulacion (puede ser NULL)
        N_efectivo = min(N_comisiones, tope) si tope IS NOT NULL else N_comisiones
        monto_plus_acumulado += SalarioPlus.monto × N_efectivo
"""

from decimal import Decimal


def calcular_total(monto_base: Decimal, plus_acumulados: list[Decimal]) -> Decimal:
    """Calcula el total de honorarios: base + suma de todos los plus.

    Args:
        monto_base: Monto base del rol docente en el período.
        plus_acumulados: Lista de subtotales de plus ya calculados
                         (cada uno = monto_plus × N_efectivo para un grupo).

    Returns:
        Total de honorarios = monto_base + Σ plus_acumulados.
    """
    return monto_base + sum(plus_acumulados, Decimal("0"))


def aplicar_tope(n_comisiones: int, tope: Decimal | None) -> int:
    """Aplica el tope de acumulación de comisiones (PA-23).

    Args:
        n_comisiones: Cantidad de comisiones detectadas del docente en el grupo.
        tope: Tope máximo de comisiones que acumulan plus.
              NULL = sin tope (acumulación ilimitada).

    Returns:
        N_efectivo = min(n_comisiones, tope) si tope IS NOT NULL, else n_comisiones.
    """
    if tope is None:
        return n_comisiones
    return min(n_comisiones, int(tope))
