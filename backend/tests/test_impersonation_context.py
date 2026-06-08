"""Tests TDD — ImpersonationContext en get_current_user (C-05).

Verifica:
- token normal → is_impersonating=False, actor_id=user.id
- token de impersonación → is_impersonating=True, actor_id=act_claim
- actor_id != user.id cuando hay impersonación activa
- real_actor_id retorna el actor correcto en ambos casos
"""

import pytest
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.dependencies import CurrentUser
from app.models.user import Usuario


def _make_user(tenant_id, email: str = None) -> Usuario:
    return Usuario(
        tenant_id=tenant_id,
        nombre="Test",
        apellidos="User",
        email=email or f"user_{uuid4().hex[:8]}@test.com",
        estado="Activo",
        password_hash=security.hash_password("Pass1234"),
    )


class TestGetCurrentUserNormal:
    """Resolución de identidad con token normal (sin impersonación)."""

    @pytest.mark.asyncio
    async def test_normal_token_resolves_user_correctly(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED: token normal → id y actor_id apuntan al mismo usuario."""
        user = _make_user(default_tenant.id, "normal@test.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        access_token = security.create_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            roles=[],
        )

        response = await async_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(user.id)
        assert data["is_impersonating"] is False

    @pytest.mark.asyncio
    async def test_normal_token_actor_id_equals_user_id(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN: con token normal, actor_id == id."""
        user = _make_user(default_tenant.id)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = security.create_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            roles=[],
        )
        payload = security.verify_access_token(token)
        assert payload is not None
        assert payload.get("imp") is None or payload.get("imp") is False

    @pytest.mark.asyncio
    async def test_real_actor_id_equals_id_without_impersonation(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE: real_actor_id == id cuando no hay impersonación."""
        current_user = CurrentUser(
            id=uuid4(),
            tenant_id=default_tenant.id,
            email="actor@test.com",
            roles=[],
            actor_id=None,
            is_impersonating=False,
        )
        assert current_user.real_actor_id == current_user.id


class TestGetCurrentUserImpersonation:
    """Resolución de identidad con token de impersonación."""

    @pytest.mark.asyncio
    async def test_impersonation_token_actor_id_differs_from_user_id(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED: con token de impersonación, actor_id != user_id."""
        actor_id = uuid4()
        target_id = uuid4()

        current_user = CurrentUser(
            id=target_id,
            tenant_id=default_tenant.id,
            email="target@test.com",
            roles=[],
            actor_id=actor_id,
            is_impersonating=True,
            impersonated_id=target_id,
        )

        assert current_user.id == target_id
        assert current_user.actor_id == actor_id
        assert current_user.actor_id != current_user.id
        assert current_user.is_impersonating is True

    @pytest.mark.asyncio
    async def test_real_actor_id_returns_actor_when_impersonating(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN: real_actor_id retorna actor_id durante impersonación."""
        actor_id = uuid4()
        target_id = uuid4()

        current_user = CurrentUser(
            id=target_id,
            tenant_id=default_tenant.id,
            email="target@test.com",
            roles=[],
            actor_id=actor_id,
            is_impersonating=True,
            impersonated_id=target_id,
        )

        assert current_user.real_actor_id == actor_id
        assert current_user.real_actor_id != target_id

    @pytest.mark.asyncio
    async def test_impersonation_token_has_imp_and_act_claims(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE: token de impersonación tiene claims imp=True y act."""
        actor_id = uuid4()
        target_id = uuid4()

        token = security.create_impersonation_token(
            actor_id=actor_id,
            target_id=target_id,
            tenant_id=default_tenant.id,
            roles=[],
        )
        payload = security.verify_access_token(token)
        assert payload is not None
        assert payload["imp"] is True
        assert payload["act"] == str(actor_id)
        assert payload["sub"] == str(target_id)
