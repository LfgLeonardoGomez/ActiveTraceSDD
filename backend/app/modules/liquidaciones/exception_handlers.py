"""Exception handlers del módulo liquidaciones (C-18, task 8.7).

Mapea las excepciones de dominio a HTTP status codes:
- LiquidacionCerradaError → 409
- VigenciaSolapadaError   → 409
- PeriodoYaCerradoError   → 409
- UsuarioNoFacturanteError → 422
- FacturaYaAbonadaError   → 409
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from app.modules.liquidaciones.exceptions import (
    FacturaYaAbonadaError,
    LiquidacionCerradaError,
    PeriodoYaCerradoError,
    UsuarioNoFacturanteError,
    VigenciaSolapadaError,
)


async def liquidacion_cerrada_handler(request: Request, exc: LiquidacionCerradaError):
    return JSONResponse(
        status_code=409,
        content={"error": "liquidacion_inmutable", "detalle": str(exc)},
    )


async def vigencia_solapada_handler(request: Request, exc: VigenciaSolapadaError):
    return JSONResponse(
        status_code=409,
        content={"error": "vigencia_solapada", "detalle": str(exc)},
    )


async def periodo_ya_cerrado_handler(request: Request, exc: PeriodoYaCerradoError):
    return JSONResponse(
        status_code=409,
        content={"error": "periodo_ya_cerrado", "detalle": str(exc)},
    )


async def usuario_no_facturante_handler(request: Request, exc: UsuarioNoFacturanteError):
    return JSONResponse(
        status_code=422,
        content={"error": "usuario_no_es_facturante", "detalle": str(exc)},
    )


async def factura_ya_abonada_handler(request: Request, exc: FacturaYaAbonadaError):
    return JSONResponse(
        status_code=409,
        content={"error": "factura_ya_abonada", "detalle": str(exc)},
    )


def register_exception_handlers(app) -> None:
    """Registra todos los exception handlers del módulo en la app FastAPI."""
    app.add_exception_handler(LiquidacionCerradaError, liquidacion_cerrada_handler)
    app.add_exception_handler(VigenciaSolapadaError, vigencia_solapada_handler)
    app.add_exception_handler(PeriodoYaCerradoError, periodo_ya_cerrado_handler)
    app.add_exception_handler(UsuarioNoFacturanteError, usuario_no_facturante_handler)
    app.add_exception_handler(FacturaYaAbonadaError, factura_ya_abonada_handler)
