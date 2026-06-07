"""Dependencies de FastAPI para inyeccion de dependencias.

C-03: get_current_user, get_current_active_user.
C-04: require_permission real con resolucion server-side.
"""

from typing import Annotated, AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.database import Base, init_db
from app.models.user import Usuario
from app.schemas.rbac_schema import PermissionContext
from app.services.permission_service import PermissionService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class CurrentUser(BaseModel):
    """Modelo Pydantic de usuario autenticado (no ORM)."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    email: str
    roles: list[str]


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency que provee una sesion async por request.

    Garantiza cierre de la sesion al finalizar la request,
    incluso ante excepcion (no fuga de conexiones al pool).
    """
    from app.core.database import AsyncSessionLocal

    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CurrentUser:
    """Resuelve identidad desde JWT verificado server-side.

    NUNCA usa parametros de request (URL, body, header custom) para identidad.
    Falla con 401 si el token es invalido o el usuario no existe/esta eliminado.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = security.verify_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str = payload.get("sub")
    tenant_id_str = payload.get("tenant_id")
    if user_id_str is None or tenant_id_str is None:
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)
        tenant_id = UUID(tenant_id_str)
    except ValueError:
        raise credentials_exception

    result = await db.execute(
        select(Usuario).where(
            Usuario.id == user_id,
            Usuario.tenant_id == tenant_id,
            Usuario.deleted_at.is_(None),
        )
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    roles = payload.get("roles", [])
    return CurrentUser(
        id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        roles=roles,
    )


async def get_current_active_user(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    """Wrapper que garantiza que el usuario no esta soft-deleted.

    get_current_user ya filtra deleted_at; este wrapper es un fail-closed
    adicional y punto de extension para futuras validaciones (ej. activo).
    """
    return current_user


def require_permission(permission: str):
    """Dependency fail-closed que verifica permisos finos server-side.

    Resuelve permisos efectivos desde la matriz rol_permiso en cada request.
    Devuelve PermissionContext con has_permission, is_propio y effective_permissions.
    Lanza 403 si el usuario no posee el permiso solicitado.
    """
    async def _check_permission(
        current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> PermissionContext:
        service = PermissionService(db, current_user.tenant_id)
        effective = await service.resolve_effective_permissions(current_user.roles)

        perm_map = {code: propio for code, propio in effective}
        has_perm = permission in perm_map

        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permiso denegado",
            )

        return PermissionContext(
            has_permission=True,
            is_propio=perm_map[permission],
            effective_permissions=set(perm_map.keys()),
        )

    return _check_permission
