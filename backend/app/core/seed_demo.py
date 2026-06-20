"""Seed de datos de ejemplo para demo/desarrollo. Idempotente.

Crea materias, una carrera, una cohorte y salarios base en el tenant default
para que las pantallas muestren contenido sin carga manual. Se ejecuta en el
lifespan tras seed_admin. No crea datos de dominio bloqueado (C-18 cálculo de
liquidaciones, PA-22/PA-23): solo catálogos y salarios base.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.estructura import Carrera, Cohorte, Materia
from app.models.tenant import Tenant
from app.modules.liquidaciones.models.salario_base import SalarioBase

_MATERIAS: list[tuple[str, str]] = [
    ("MAT-101", "Análisis Matemático I"),
    ("PRG-101", "Programación I"),
    ("FIS-101", "Física I"),
]

_SALARIOS_BASE: list[tuple[str, Decimal]] = [
    ("PROFESOR", Decimal("500000.00")),
    ("TUTOR", Decimal("300000.00")),
]


async def seed_demo(db: AsyncSession) -> None:
    """Crea datos de ejemplo si no existen. Idempotente (safe to re-run)."""
    result = await db.execute(
        select(Tenant).where(Tenant.slug == "default").limit(1)
    )
    tenant = result.scalar_one_or_none()
    if tenant is None:
        return
    tid = tenant.id

    # Materias del catálogo
    for codigo, nombre in _MATERIAS:
        existing = await db.execute(
            select(Materia.id).where(
                Materia.tenant_id == tid,
                Materia.codigo == codigo,
                Materia.deleted_at.is_(None),
            )
        )
        if existing.scalar_one_or_none() is None:
            db.add(
                Materia(tenant_id=tid, codigo=codigo, nombre=nombre, estado="Activa")
            )

    # Carrera + cohorte
    result = await db.execute(
        select(Carrera).where(
            Carrera.tenant_id == tid,
            Carrera.codigo == "ING-SIS",
            Carrera.deleted_at.is_(None),
        )
    )
    carrera = result.scalar_one_or_none()
    if carrera is None:
        carrera = Carrera(
            tenant_id=tid,
            codigo="ING-SIS",
            nombre="Ingeniería en Sistemas",
            estado="Activa",
        )
        db.add(carrera)
        await db.flush()  # need carrera.id for the cohorte FK

    existing = await db.execute(
        select(Cohorte.id).where(
            Cohorte.tenant_id == tid,
            Cohorte.carrera_id == carrera.id,
            Cohorte.nombre == "Cohorte 2026",
            Cohorte.deleted_at.is_(None),
        )
    )
    if existing.scalar_one_or_none() is None:
        db.add(
            Cohorte(
                tenant_id=tid,
                carrera_id=carrera.id,
                nombre="Cohorte 2026",
                anio=2026,
                vig_desde=date(2026, 3, 1),
                estado="Activa",
            )
        )

    # Salarios base por rol
    for rol, monto in _SALARIOS_BASE:
        existing = await db.execute(
            select(SalarioBase.id).where(
                SalarioBase.tenant_id == tid,
                SalarioBase.rol == rol,
                SalarioBase.deleted_at.is_(None),
            )
        )
        if existing.scalar_one_or_none() is None:
            db.add(
                SalarioBase(
                    tenant_id=tid,
                    rol=rol,
                    monto=monto,
                    desde=date(2026, 1, 1),
                )
            )

    await db.commit()
