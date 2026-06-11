"""Bootstrap de la aplicación FastAPI.

IMPLEMENTADO en C-01: lifespan, middleware, logging, OTel, health router.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import Settings
from app.core.database import init_db
from app.core.logging import init_logging
from app.core.observability import init_observability
from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.health import router as health_router
from app.api.v1.routers.rbac import (
    router_permisos,
    router_roles,
    router_rol_permisos,
)
from app.api.v1.routers.usuarios import router as usuarios_router
from app.api.v1.routers.asignaciones import router as asignaciones_router
from app.api.v1.routers.equipos import router as equipos_router
from app.api.v1.routers.padron import router as padron_router
from app.api.v1.routers.encuentros import router as encuentros_router
from app.api.v1.routers.guardias import router as guardias_router
from app.api.v1.routers.calificaciones import router as calificaciones_router
from app.api.v1.routers.umbral import router as umbral_router
from app.api.v1.routers.analisis import router as analisis_router
from app.api.v1.routers.comunicaciones import router as comunicaciones_router
from app.api.v1.routers.coloquios import router as coloquios_router
from app.api.v1.routers.avisos import router as avisos_router
from app.api.v1.routers.tareas import router as tareas_router
from app.api.v1.routers.programas import router as programas_router
from app.api.v1.routers.fechas_academicas import router as fechas_academicas_router

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan: init en arranque, cleanup en shutdown."""
    init_db(settings.database_url)
    init_logging()
    init_observability(app)
    yield


app = FastAPI(
    title="activia-trace",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router, tags=["health"])
app.include_router(auth_router)
app.include_router(router_roles)
app.include_router(router_permisos)
app.include_router(router_rol_permisos)
app.include_router(usuarios_router)
app.include_router(asignaciones_router)
app.include_router(equipos_router)
app.include_router(padron_router)
app.include_router(encuentros_router)
app.include_router(guardias_router)
app.include_router(calificaciones_router)
app.include_router(umbral_router)
app.include_router(analisis_router)
app.include_router(comunicaciones_router)
app.include_router(coloquios_router)
app.include_router(avisos_router)
app.include_router(tareas_router)
app.include_router(programas_router)
app.include_router(fechas_academicas_router)
