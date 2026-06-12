"""Router de edición de perfil propio (C-20).

Endpoint:
- PATCH /api/v1/perfil → editar perfil del usuario autenticado.

Reglas duras:
- Identidad desde JWT, nunca desde URL/body.
- Guard require_permission("perfil:editar").
- Thin router: valida input, delega a service, registra auditoría.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    CurrentUser,
    get_current_active_user,
    get_db,
    require_permission,
)
from app.schemas.perfil import PerfilUpdate
from app.schemas.usuarios import UsuarioDetailRead
from app.services.perfil_service import PerfilService

router = APIRouter(
    prefix="/api/v1/perfil",
    tags=["perfil"],
    responses={
        403: {"description": "Permiso denegado"},
        404: {"description": "Usuario no encontrado"},
        422: {"description": "Validación fallida"},
    },
)


@router.patch(
    "",
    response_model=UsuarioDetailRead,
    status_code=status.HTTP_200_OK,
)
async def editar_perfil(
    body: PerfilUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[None, Depends(require_permission("perfil:editar"))],
) -> UsuarioDetailRead:
    """Edita el perfil del usuario autenticado."""
    service = PerfilService(db, current_user.tenant_id, current_user.id)
    data = body.model_dump(exclude_unset=True)
    usuario = await service.editar_perfil(data)
    return UsuarioDetailRead.model_validate(usuario)
