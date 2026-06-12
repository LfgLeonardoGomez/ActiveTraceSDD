"""Tests de excepciones del módulo liquidaciones (C-18)."""

import pytest


def test_liquidacion_cerrada_error():
    from app.modules.liquidaciones.exceptions import LiquidacionCerradaError

    from uuid import uuid4
    lid = uuid4()
    exc = LiquidacionCerradaError(lid)
    assert str(lid) in str(exc)
    assert exc.liquidacion_id == lid


def test_vigencia_solapada_error():
    from app.modules.liquidaciones.exceptions import VigenciaSolapadaError

    from uuid import uuid4
    rid = uuid4()
    exc = VigenciaSolapadaError("salarios_base", rid)
    assert "salarios_base" in str(exc)
    assert exc.tabla == "salarios_base"
    assert exc.registro_id == rid


def test_periodo_ya_cerrado_error():
    from app.modules.liquidaciones.exceptions import PeriodoYaCerradoError

    from uuid import uuid4
    cid = uuid4()
    exc = PeriodoYaCerradoError(cid, "2026-03")
    assert "2026-03" in str(exc)
    assert exc.periodo == "2026-03"


def test_usuario_no_facturante_error():
    from app.modules.liquidaciones.exceptions import UsuarioNoFacturanteError

    from uuid import uuid4
    uid = uuid4()
    exc = UsuarioNoFacturanteError(uid)
    assert exc.usuario_id == uid


def test_factura_ya_abonada_error():
    from app.modules.liquidaciones.exceptions import FacturaYaAbonadaError

    from uuid import uuid4
    fid = uuid4()
    exc = FacturaYaAbonadaError(fid)
    assert exc.factura_id == fid
