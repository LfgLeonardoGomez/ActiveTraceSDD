"""Seed de datos de ejemplo para demo/desarrollo. Idempotente.

Crea materias, una carrera, una cohorte y salarios base en el tenant default
para que las pantallas muestren contenido sin carga manual. Se ejecuta en el
lifespan tras seed_admin. No crea datos de dominio bloqueado (C-18 cálculo de
liquidaciones, PA-22/PA-23): solo catálogos y salarios base.

También crea una comisión completa y gradable (Asignacion PROFESOR + VersionPadron
+ EntradaPadron × 6 + Calificaciones para TP1/TP2/Parcial 1) usando al admin
como docente/importador, de forma totalmente idempotente.
"""

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encrypt_pii
from app.models.asignacion import Asignacion
from app.models.calificacion import Calificacion
from app.models.estructura import Carrera, Cohorte, Materia
from app.models.padron import EntradaPadron, VersionPadron
from app.models.tenant import Tenant
from app.models.user import Usuario
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

# Seed students: (nombre, apellidos, email_plain, comision, regional)
_STUDENTS: list[tuple[str, str, str, str, str]] = [
    ("Ana", "García", "ana.garcia@demo.edu", "A", "Centro"),
    ("Bruno", "López", "bruno.lopez@demo.edu", "A", "Centro"),
    ("Carla", "Martínez", "carla.martinez@demo.edu", "A", "Centro"),
    ("Diego", "Rodríguez", "diego.rodriguez@demo.edu", "A", "Centro"),
    ("Elena", "Fernández", "elena.fernandez@demo.edu", "A", "Centro"),
    ("Fabio", "Torres", "fabio.torres@demo.edu", "A", "Centro"),
]

# Grades per student × activity.
# None means the student has no grade (appears as "atrasado" in analytics).
# Varied notes 4..10 so ranking has meaningful spread.
# Students 4 and 5 (Diego, Elena) are missing some grades intentionally.
_ACTIVITIES = ["TP1", "TP2", "Parcial 1"]

_GRADES: list[list[float | None]] = [
    # Ana:    TP1=8, TP2=9, Parcial=7   — full, good student
    [8.0, 9.0, 7.0],
    # Bruno:  TP1=6, TP2=5, Parcial=4   — full, struggling
    [6.0, 5.0, 4.0],
    # Carla:  TP1=10, TP2=10, Parcial=9 — full, top student
    [10.0, 10.0, 9.0],
    # Diego:  TP1=7, TP2=None, Parcial=None — missing 2 activities (atrasado)
    [7.0, None, None],
    # Elena:  TP1=None, TP2=6, Parcial=None — missing 2 activities (atrasada)
    [None, 6.0, None],
    # Fabio:  TP1=5, TP2=4, Parcial=6   — full, borderline
    [5.0, 4.0, 6.0],
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

    # Flush so MAT-101 has an id before joining
    await db.flush()

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

    await db.flush()

    # ------------------------------------------------------------------
    # Comisión demo: requires admin user + MAT-101 + Cohorte 2026
    # ------------------------------------------------------------------
    await _seed_comision(db, tid)

    await db.commit()


async def _seed_comision(db: AsyncSession, tid) -> None:
    """Seed idempotente de la comisión demo (Asignacion + padrón + calificaciones).

    Decision ya ratificada: comision = Asignacion (docente↔materia↔cohorte).
    PA-01 interpretada (no cerrada): usamos MAT-101 + Cohorte 2026 + ING-SIS.
    El admin es el docente/importador para que el scope pase titularidad.
    """
    # Fetch admin user (the one with an ADMIN asignacion in this tenant)
    admin_result = await db.execute(
        select(Usuario)
        .join(Asignacion, Asignacion.usuario_id == Usuario.id)
        .where(
            Asignacion.tenant_id == tid,
            Asignacion.rol == "ADMIN",
            Asignacion.deleted_at.is_(None),
            Usuario.tenant_id == tid,
            Usuario.deleted_at.is_(None),
        )
        .limit(1)
    )
    admin = admin_result.scalar_one_or_none()
    if admin is None:
        # seed_admin hasn't run yet or tenant has no admin — skip gracefully
        return

    # Fetch MAT-101
    mat_result = await db.execute(
        select(Materia).where(
            Materia.tenant_id == tid,
            Materia.codigo == "MAT-101",
            Materia.deleted_at.is_(None),
        )
    )
    materia = mat_result.scalar_one_or_none()
    if materia is None:
        return  # shouldn't happen — seeded above

    # Fetch Cohorte 2026
    cohorte_result = await db.execute(
        select(Cohorte).where(
            Cohorte.tenant_id == tid,
            Cohorte.nombre == "Cohorte 2026",
            Cohorte.deleted_at.is_(None),
        )
    )
    cohorte = cohorte_result.scalar_one_or_none()
    if cohorte is None:
        return  # shouldn't happen — seeded above

    # Fetch ING-SIS carrera
    carrera_result = await db.execute(
        select(Carrera).where(
            Carrera.tenant_id == tid,
            Carrera.codigo == "ING-SIS",
            Carrera.deleted_at.is_(None),
        )
    )
    carrera = carrera_result.scalar_one_or_none()
    if carrera is None:
        return

    # ------------------------------------------------------------------
    # 1. Asignacion PROFESOR (idempotent)
    # ------------------------------------------------------------------
    asig_result = await db.execute(
        select(Asignacion).where(
            Asignacion.tenant_id == tid,
            Asignacion.usuario_id == admin.id,
            Asignacion.materia_id == materia.id,
            Asignacion.cohorte_id == cohorte.id,
            Asignacion.deleted_at.is_(None),
        )
    )
    asignacion = asig_result.scalar_one_or_none()
    if asignacion is None:
        asignacion = Asignacion(
            tenant_id=tid,
            usuario_id=admin.id,
            rol="PROFESOR",
            materia_id=materia.id,
            carrera_id=carrera.id,
            cohorte_id=cohorte.id,
            desde=date(2026, 3, 1),
            hasta=None,
        )
        db.add(asignacion)
        await db.flush()  # need asignacion.id

    # ------------------------------------------------------------------
    # 2. VersionPadron (idempotent — one active version per materia×cohorte)
    # ------------------------------------------------------------------
    version_result = await db.execute(
        select(VersionPadron).where(
            VersionPadron.tenant_id == tid,
            VersionPadron.materia_id == materia.id,
            VersionPadron.cohorte_id == cohorte.id,
            VersionPadron.origen == "seed",
            VersionPadron.deleted_at.is_(None),
        )
    )
    version = version_result.scalar_one_or_none()
    if version is None:
        version = VersionPadron(
            tenant_id=tid,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            cargado_por=admin.id,
            cargado_at=datetime.now(timezone.utc),
            activa=True,
            origen="seed",
        )
        db.add(version)
        await db.flush()  # need version.id for EntradaPadron FKs

    # ------------------------------------------------------------------
    # 3. EntradaPadron × 6 (idempotent per email ciphertext would be fragile,
    #    so we check by version_id count — if entries exist, skip entirely)
    # ------------------------------------------------------------------
    entries_count_result = await db.execute(
        select(EntradaPadron)
        .where(
            EntradaPadron.tenant_id == tid,
            EntradaPadron.version_id == version.id,
            EntradaPadron.deleted_at.is_(None),
        )
    )
    existing_entries = list(entries_count_result.scalars().all())

    if not existing_entries:
        now = datetime.now(timezone.utc)
        entries = []
        for nombre, apellidos, email_plain, comision, regional in _STUDENTS:
            entry = EntradaPadron(
                tenant_id=tid,
                version_id=version.id,
                usuario_id=None,
                nombre=nombre,
                apellidos=apellidos,
                # AES-256-GCM encrypted — consistent with PadronRepository convention
                email=encrypt_pii(email_plain),
                comision=comision,
                regional=regional,
            )
            db.add(entry)
            entries.append(entry)
        await db.flush()  # need entry.id for Calificacion FKs

        # ------------------------------------------------------------------
        # 4. Calificaciones (only created alongside entries — idempotent block)
        # ------------------------------------------------------------------
        now = datetime.now(timezone.utc)
        for idx, entry in enumerate(entries):
            for act_idx, actividad in enumerate(_ACTIVITIES):
                nota = _GRADES[idx][act_idx]
                if nota is None:
                    # Missing grade — student is "atrasado" for this activity
                    continue
                aprobado = nota >= 6.0
                cal = Calificacion(
                    tenant_id=tid,
                    entrada_padron_id=entry.id,
                    materia_id=materia.id,
                    usuario_importador_id=admin.id,
                    actividad=actividad,
                    nota_numerica=nota,
                    nota_textual=None,
                    aprobado=aprobado,
                    origen="seed",
                    importado_at=now,
                )
                db.add(cal)
