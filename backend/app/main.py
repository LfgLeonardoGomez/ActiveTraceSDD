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
