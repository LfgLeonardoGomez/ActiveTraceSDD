"""Módulo de liquidaciones y honorarios docentes (C-18).

Expone el router combinado para registrar en app/main.py.
"""

from fastapi import APIRouter

from app.modules.liquidaciones.routers.salario_base_router import router as salario_base_router
from app.modules.liquidaciones.routers.salario_plus_router import router as salario_plus_router
from app.modules.liquidaciones.routers.materia_grupo_plus_router import router as mgp_router
from app.modules.liquidaciones.routers.liquidaciones_router import router as liquidaciones_router
from app.modules.liquidaciones.routers.facturas_router import router as facturas_router

# Router combinado del módulo
router = APIRouter()
router.include_router(salario_base_router)
router.include_router(salario_plus_router)
router.include_router(mgp_router)
router.include_router(liquidaciones_router)
router.include_router(facturas_router)

__all__ = ["router"]
