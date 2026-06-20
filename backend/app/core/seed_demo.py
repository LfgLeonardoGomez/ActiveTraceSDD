"""Seed de datos de ejemplo para demo/desarrollo. Idempotente.

Crea materias, una carrera, una cohorte y salarios base en el tenant default
para que las pantallas muestren contenido sin carga manual. Se ejecuta en el
lifespan tras seed_admin. No crea datos de dominio bloqueado (C-18 cálculo de
liquidaciones, PA-22/PA-23): solo catálogos y salarios base.

También crea una comisión completa y gradable (Asignacion PROFESOR + VersionPadron
+ EntradaPadron × 6 + Calificaciones para TP1/TP2/Parcial 1) usando al admin
como docente/importador, de forma totalmente idempotente.

Bloques adicionales (idempotentes):
- 3 docentes demo (María González, Carlos López, Laura Ruiz)
- 2da comisión PRG-101 con María como PROFESOR, 6 alumnos comisión B
- Encuentros: 2 SlotEncuentro + 4 InstanciaEncuentro por slot
- Guardias: 2 Guardia (Laura y María como tutor)
- Tareas: 3 Tarea asignadas a Carlos + 1 ComentarioTarea cada una
- Avisos: 3 Aviso variados (Global / PorMateria)
- Comunicaciones: 1 lote de mensajes pendientes para alumnos de comisión A
- Coloquios: 1 Evaluacion MAT-101 + candidatos + reservas + resultados
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encrypt_pii, hash_email_for_lookup
from app.models.asignacion import Asignacion
from app.models.aviso import Aviso, AlcanceAviso, SeveridadAviso
from app.models.calificacion import Calificacion
from app.models.comunicacion import Comunicacion
from app.models.estructura import Carrera, Cohorte, Materia
from app.models.evaluacion import (
    Evaluacion,
    EvaluacionCandidato,
    ReservaEvaluacion,
    ResultadoEvaluacion,
    TipoEvaluacion,
    EstadoReserva,
)
from app.models.guardia import Guardia
from app.models.instancia_encuentro import InstanciaEncuentro
from app.models.padron import EntradaPadron, VersionPadron
from app.models.slot_encuentro import SlotEncuentro
from app.models.tarea import ComentarioTarea, EstadoTarea, Tarea
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

    # ------------------------------------------------------------------
    # Bloques adicionales — todos idempotentes
    # ------------------------------------------------------------------
    await _seed_docentes(db, tid)
    await _seed_comision_b(db, tid)
    await _seed_encuentros(db, tid)
    await _seed_guardias(db, tid)
    await _seed_tareas(db, tid)
    await _seed_avisos(db, tid)
    await _seed_comunicaciones(db, tid)
    await _seed_coloquios(db, tid)

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


# ---------------------------------------------------------------------------
# Docentes demo
# ---------------------------------------------------------------------------

# (nombre, apellidos, email_plain, estado)
_DOCENTES: list[tuple[str, str, str, str]] = [
    ("María", "González", "maria.gonzalez@demo.edu", "activo"),
    ("Carlos", "López", "carlos.lopez@demo.edu", "activo"),
    ("Laura", "Ruiz", "laura.ruiz@demo.edu", "activo"),
]


async def _seed_docentes(db: AsyncSession, tid) -> None:
    """Crea 3 docentes demo. Idempotente por email_hash."""
    for nombre, apellidos, email_plain, estado in _DOCENTES:
        email_hash = hash_email_for_lookup(email_plain)
        existing = await db.execute(
            select(Usuario.id).where(
                Usuario.tenant_id == tid,
                Usuario.email_hash == email_hash,
                Usuario.deleted_at.is_(None),
            )
        )
        if existing.scalar_one_or_none() is None:
            db.add(
                Usuario(
                    tenant_id=tid,
                    nombre=nombre,
                    apellidos=apellidos,
                    email=encrypt_pii(email_plain),
                    email_hash=email_hash,
                    estado=estado,
                )
            )
    await db.flush()


# ---------------------------------------------------------------------------
# 2da comisión PRG-101 (comisión B, María como PROFESOR)
# ---------------------------------------------------------------------------

_STUDENTS_B: list[tuple[str, str, str, str, str]] = [
    ("Hugo", "Blanco", "hugo.blanco@demo.edu", "B", "Norte"),
    ("Iris", "Castro", "iris.castro@demo.edu", "B", "Norte"),
    ("Juan", "Delgado", "juan.delgado@demo.edu", "B", "Norte"),
    ("Karen", "Espinoza", "karen.espinoza@demo.edu", "B", "Norte"),
    ("Luis", "Fuentes", "luis.fuentes@demo.edu", "B", "Norte"),
    ("Marta", "Gómez", "marta.gomez@demo.edu", "B", "Norte"),
]

_ACTIVITIES_B = ["TP1", "TP2", "Parcial 1"]

# Hugo/Iris/Juan: grades full; Karen/Luis: missing grades (atrasados); Marta: full
_GRADES_B: list[list[float | None]] = [
    [9.0, 8.0, 7.0],   # Hugo: full, good
    [6.0, 7.0, 8.0],   # Iris: full, improving
    [10.0, 9.0, 10.0], # Juan: full, top
    [5.0, None, None],  # Karen: missing TP2 and Parcial (atrasada)
    [None, 4.0, None],  # Luis: missing TP1 and Parcial (atrasado)
    [7.0, 6.0, 5.0],   # Marta: full, borderline
]


async def _seed_comision_b(db: AsyncSession, tid) -> None:
    """Seed idempotente de la 2da comisión demo (PRG-101 + María como PROFESOR)."""
    # Fetch María
    maria_hash = hash_email_for_lookup("maria.gonzalez@demo.edu")
    maria_result = await db.execute(
        select(Usuario).where(
            Usuario.tenant_id == tid,
            Usuario.email_hash == maria_hash,
            Usuario.deleted_at.is_(None),
        )
    )
    maria = maria_result.scalar_one_or_none()
    if maria is None:
        return  # _seed_docentes must run first

    # Fetch admin (used as importador for calificaciones)
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
        return

    # Fetch PRG-101
    prg_result = await db.execute(
        select(Materia).where(
            Materia.tenant_id == tid,
            Materia.codigo == "PRG-101",
            Materia.deleted_at.is_(None),
        )
    )
    materia = prg_result.scalar_one_or_none()
    if materia is None:
        return

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
        return

    # Fetch ING-SIS
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

    # Asignacion PROFESOR María ↔ PRG-101 (idempotent)
    asig_result = await db.execute(
        select(Asignacion).where(
            Asignacion.tenant_id == tid,
            Asignacion.usuario_id == maria.id,
            Asignacion.materia_id == materia.id,
            Asignacion.cohorte_id == cohorte.id,
            Asignacion.deleted_at.is_(None),
        )
    )
    if asig_result.scalar_one_or_none() is None:
        db.add(
            Asignacion(
                tenant_id=tid,
                usuario_id=maria.id,
                rol="PROFESOR",
                materia_id=materia.id,
                carrera_id=carrera.id,
                cohorte_id=cohorte.id,
                desde=date(2026, 3, 1),
                hasta=None,
            )
        )
        await db.flush()

    # VersionPadron PRG-101 (idempotent — one active seed version per materia×cohorte)
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
        await db.flush()

    # EntradaPadron × 6 comisión B (idempotent: skip if any entries exist)
    entries_result = await db.execute(
        select(EntradaPadron).where(
            EntradaPadron.tenant_id == tid,
            EntradaPadron.version_id == version.id,
            EntradaPadron.deleted_at.is_(None),
        )
    )
    existing_entries = list(entries_result.scalars().all())

    if not existing_entries:
        now = datetime.now(timezone.utc)
        entries_b = []
        for nombre, apellidos, email_plain, comision, regional in _STUDENTS_B:
            entry = EntradaPadron(
                tenant_id=tid,
                version_id=version.id,
                usuario_id=None,
                nombre=nombre,
                apellidos=apellidos,
                email=encrypt_pii(email_plain),
                comision=comision,
                regional=regional,
            )
            db.add(entry)
            entries_b.append(entry)
        await db.flush()

        # Calificaciones comisión B
        now = datetime.now(timezone.utc)
        for idx, entry in enumerate(entries_b):
            for act_idx, actividad in enumerate(_ACTIVITIES_B):
                nota = _GRADES_B[idx][act_idx]
                if nota is None:
                    continue
                aprobado = nota >= 6.0
                db.add(
                    Calificacion(
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
                )


# ---------------------------------------------------------------------------
# Encuentros
# ---------------------------------------------------------------------------


async def _seed_encuentros(db: AsyncSession, tid) -> None:
    """Crea 2 SlotEncuentro (MAT-101 y PRG-101) con 4 InstanciaEncuentro cada uno."""
    # Fetch admin as creador for MAT-101 slot
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
        return

    # Fetch María as creador for PRG-101 slot
    maria_hash = hash_email_for_lookup("maria.gonzalez@demo.edu")
    maria_result = await db.execute(
        select(Usuario).where(
            Usuario.tenant_id == tid,
            Usuario.email_hash == maria_hash,
            Usuario.deleted_at.is_(None),
        )
    )
    maria = maria_result.scalar_one_or_none()
    if maria is None:
        return

    # Fetch materias
    mat_result = await db.execute(
        select(Materia).where(
            Materia.tenant_id == tid,
            Materia.codigo == "MAT-101",
            Materia.deleted_at.is_(None),
        )
    )
    mat101 = mat_result.scalar_one_or_none()

    prg_result = await db.execute(
        select(Materia).where(
            Materia.tenant_id == tid,
            Materia.codigo == "PRG-101",
            Materia.deleted_at.is_(None),
        )
    )
    prg101 = prg_result.scalar_one_or_none()

    if mat101 is None or prg101 is None:
        return

    # Fetch carrera + cohorte
    carrera_result = await db.execute(
        select(Carrera).where(
            Carrera.tenant_id == tid,
            Carrera.codigo == "ING-SIS",
            Carrera.deleted_at.is_(None),
        )
    )
    carrera = carrera_result.scalar_one_or_none()

    cohorte_result = await db.execute(
        select(Cohorte).where(
            Cohorte.tenant_id == tid,
            Cohorte.nombre == "Cohorte 2026",
            Cohorte.deleted_at.is_(None),
        )
    )
    cohorte = cohorte_result.scalar_one_or_none()

    if carrera is None or cohorte is None:
        return

    # Slots: one per materia (idempotent by titulo + materia)
    _slots_def = [
        # (titulo, materia, creador, dia_semana, hora, fecha_inicio, cant_semanas, meet_url)
        (
            "Encuentro semanal MAT-101",
            mat101,
            admin,
            1,  # lunes
            "10:00",
            date(2026, 3, 2),
            16,
            "https://meet.google.com/mat101-demo",
        ),
        (
            "Encuentro semanal PRG-101",
            prg101,
            maria,
            3,  # miércoles
            "14:00",
            date(2026, 3, 4),
            16,
            "https://meet.google.com/prg101-demo",
        ),
    ]

    for titulo, materia, creador, dia_semana, hora, fecha_inicio, cant_semanas, meet_url in _slots_def:
        slot_check = await db.execute(
            select(SlotEncuentro).where(
                SlotEncuentro.tenant_id == tid,
                SlotEncuentro.materia_id == materia.id,
                SlotEncuentro.titulo == titulo,
                SlotEncuentro.deleted_at.is_(None),
            )
        )
        slot = slot_check.scalar_one_or_none()
        if slot is None:
            slot = SlotEncuentro(
                tenant_id=tid,
                creador_id=creador.id,
                materia_id=materia.id,
                carrera_id=carrera.id,
                cohorte_id=cohorte.id,
                titulo=titulo,
                dia_semana=dia_semana,
                hora=hora,
                fecha_inicio=fecha_inicio,
                cant_semanas=cant_semanas,
                meet_url=meet_url,
            )
            db.add(slot)
            await db.flush()

            # 4 InstanciaEncuentro weekly from fecha_inicio
            for week in range(4):
                inst_fecha = fecha_inicio + timedelta(weeks=week)
                db.add(
                    InstanciaEncuentro(
                        tenant_id=tid,
                        slot_id=slot.id,
                        materia_id=materia.id,
                        titulo=f"{titulo} — Semana {week + 1}",
                        fecha=inst_fecha,
                        hora=hora,
                        estado="Programado",
                        meet_url=meet_url,
                    )
                )


# ---------------------------------------------------------------------------
# Guardias
# ---------------------------------------------------------------------------


async def _seed_guardias(db: AsyncSession, tid) -> None:
    """Crea 2 Guardia (Laura y María como tutores). Idempotente por tutor+fecha."""
    laura_hash = hash_email_for_lookup("laura.ruiz@demo.edu")
    maria_hash = hash_email_for_lookup("maria.gonzalez@demo.edu")

    users_result = await db.execute(
        select(Usuario).where(
            Usuario.tenant_id == tid,
            Usuario.email_hash.in_([laura_hash, maria_hash]),
            Usuario.deleted_at.is_(None),
        )
    )
    users = {u.email_hash: u for u in users_result.scalars().all()}
    laura = users.get(laura_hash)
    maria = users.get(maria_hash)
    if laura is None or maria is None:
        return

    mat_result = await db.execute(
        select(Materia).where(
            Materia.tenant_id == tid,
            Materia.codigo.in_(["MAT-101", "PRG-101"]),
            Materia.deleted_at.is_(None),
        )
    )
    mats = {m.codigo: m for m in mat_result.scalars().all()}
    mat101 = mats.get("MAT-101")
    prg101 = mats.get("PRG-101")
    if mat101 is None or prg101 is None:
        return

    carrera_result = await db.execute(
        select(Carrera).where(
            Carrera.tenant_id == tid,
            Carrera.codigo == "ING-SIS",
            Carrera.deleted_at.is_(None),
        )
    )
    carrera = carrera_result.scalar_one_or_none()
    cohorte_result = await db.execute(
        select(Cohorte).where(
            Cohorte.tenant_id == tid,
            Cohorte.nombre == "Cohorte 2026",
            Cohorte.deleted_at.is_(None),
        )
    )
    cohorte = cohorte_result.scalar_one_or_none()
    if carrera is None or cohorte is None:
        return

    _guardias_def = [
        # (tutor, materia, fecha, horario, descripcion)
        (laura, mat101, date(2026, 4, 7), "09:00-11:00", "Guardia de atención MAT-101"),
        (maria, prg101, date(2026, 4, 9), "14:00-16:00", "Guardia de atención PRG-101"),
    ]

    for tutor, materia, fecha, horario, descripcion in _guardias_def:
        check = await db.execute(
            select(Guardia.id).where(
                Guardia.tenant_id == tid,
                Guardia.tutor_id == tutor.id,
                Guardia.materia_id == materia.id,
                Guardia.fecha == fecha,
                Guardia.deleted_at.is_(None),
            )
        )
        if check.scalar_one_or_none() is None:
            db.add(
                Guardia(
                    tenant_id=tid,
                    tutor_id=tutor.id,
                    materia_id=materia.id,
                    carrera_id=carrera.id,
                    cohorte_id=cohorte.id,
                    fecha=fecha,
                    horario=horario,
                    descripcion=descripcion,
                    estado="Pendiente",
                )
            )


# ---------------------------------------------------------------------------
# Tareas
# ---------------------------------------------------------------------------


async def _seed_tareas(db: AsyncSession, tid) -> None:
    """Crea 3 Tarea asignadas a Carlos + 1 ComentarioTarea cada una."""
    carlos_hash = hash_email_for_lookup("carlos.lopez@demo.edu")
    carlos_result = await db.execute(
        select(Usuario).where(
            Usuario.tenant_id == tid,
            Usuario.email_hash == carlos_hash,
            Usuario.deleted_at.is_(None),
        )
    )
    carlos = carlos_result.scalar_one_or_none()
    if carlos is None:
        return

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
        return

    mat_result = await db.execute(
        select(Materia).where(
            Materia.tenant_id == tid,
            Materia.codigo == "MAT-101",
            Materia.deleted_at.is_(None),
        )
    )
    mat101 = mat_result.scalar_one_or_none()

    _tareas_def = [
        # (titulo, descripcion, criterio_cierre, materia_id)
        (
            "Revisar correcciones de TP1",
            "Verificar las correcciones manuales del TP1 de comisión A antes del cierre.",
            "Todas las calificaciones de TP1 revisadas y confirmadas.",
            mat101.id if mat101 else None,
        ),
        (
            "Actualizar material didáctico",
            "Subir el material actualizado al campus virtual para el parcial.",
            "Material disponible en Moodle con al menos 5 días de anticipación.",
            mat101.id if mat101 else None,
        ),
        (
            "Completar actas de coloquio",
            "Registrar los resultados del último coloquio en el sistema.",
            "Resultados cargados y firmados digitalmente.",
            None,
        ),
    ]

    for titulo, descripcion, criterio_cierre, materia_id in _tareas_def:
        check = await db.execute(
            select(Tarea.id).where(
                Tarea.tenant_id == tid,
                Tarea.titulo == titulo,
                Tarea.asignado_a == carlos.id,
                Tarea.deleted_at.is_(None),
            )
        )
        if check.scalar_one_or_none() is None:
            tarea = Tarea(
                tenant_id=tid,
                titulo=titulo,
                descripcion=descripcion,
                criterio_cierre=criterio_cierre,
                estado=EstadoTarea.PENDIENTE.value,
                aprobada=False,
                devuelta=False,
                asignado_a=carlos.id,
                asignado_por=admin.id,
                materia_id=materia_id,
            )
            db.add(tarea)
            await db.flush()  # need tarea.id for comentario FK

            db.add(
                ComentarioTarea(
                    tenant_id=tid,
                    tarea_id=tarea.id,
                    autor_id=admin.id,
                    contenido="Tarea creada en el seed demo. Por favor revisar con prioridad.",
                )
            )


# ---------------------------------------------------------------------------
# Avisos
# ---------------------------------------------------------------------------


async def _seed_avisos(db: AsyncSession, tid) -> None:
    """Crea 3 Aviso variados (Global / PorMateria). Idempotente por titulo."""
    mat_result = await db.execute(
        select(Materia).where(
            Materia.tenant_id == tid,
            Materia.codigo.in_(["MAT-101", "PRG-101"]),
            Materia.deleted_at.is_(None),
        )
    )
    mats = {m.codigo: m for m in mat_result.scalars().all()}
    mat101 = mats.get("MAT-101")
    prg101 = mats.get("PRG-101")

    now = datetime.now(timezone.utc)
    fin = now + timedelta(days=30)

    _avisos_def = [
        # (titulo, cuerpo, alcance, materia_id, severidad, orden)
        (
            "Bienvenida al ciclo 2026",
            "Les damos la bienvenida al ciclo lectivo 2026. El inicio de clases es el 3 de marzo.",
            AlcanceAviso.GLOBAL.value,
            None,
            SeveridadAviso.INFO.value,
            0,
        ),
        (
            "Cambio de fecha parcial MAT-101",
            "El parcial de Análisis Matemático I se reprograma para el 15 de mayo.",
            AlcanceAviso.POR_MATERIA.value,
            mat101.id if mat101 else None,
            SeveridadAviso.ADVERTENCIA.value,
            1,
        ),
        (
            "Cierre de inscripciones PRG-101",
            "Las inscripciones al coloquio de Programación I cierran el viernes a las 23:59.",
            AlcanceAviso.POR_MATERIA.value,
            prg101.id if prg101 else None,
            SeveridadAviso.CRITICO.value,
            2,
        ),
    ]

    for titulo, cuerpo, alcance, materia_id, severidad, orden in _avisos_def:
        check = await db.execute(
            select(Aviso.id).where(
                Aviso.tenant_id == tid,
                Aviso.titulo == titulo,
                Aviso.deleted_at.is_(None),
            )
        )
        if check.scalar_one_or_none() is None:
            db.add(
                Aviso(
                    tenant_id=tid,
                    alcance=alcance,
                    materia_id=materia_id,
                    severidad=severidad,
                    titulo=titulo,
                    cuerpo=cuerpo,
                    inicio_en=now,
                    fin_en=fin,
                    orden=orden,
                    activo=True,
                    requiere_ack=False,
                )
            )


# ---------------------------------------------------------------------------
# Comunicaciones
# ---------------------------------------------------------------------------


async def _seed_comunicaciones(db: AsyncSession, tid) -> None:
    """Crea un lote de Comunicacion Pendiente para alumnos de comisión A.

    Idempotente: skip if any Comunicacion already exists for this tenant with
    the demo asunto prefix (one batch is enough for demo purposes).
    """
    _DEMO_ASUNTO = "[Demo] Aviso de actividad pendiente"

    check = await db.execute(
        select(Comunicacion.id).where(
            Comunicacion.tenant_id == tid,
            Comunicacion.asunto == _DEMO_ASUNTO,
            Comunicacion.deleted_at.is_(None),
        )
    )
    if check.first() is not None:
        return  # already seeded

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
        return

    mat_result = await db.execute(
        select(Materia).where(
            Materia.tenant_id == tid,
            Materia.codigo == "MAT-101",
            Materia.deleted_at.is_(None),
        )
    )
    mat101 = mat_result.scalar_one_or_none()
    if mat101 is None:
        return

    lote_id = uuid4()
    _cuerpo = (
        "Este es un mensaje demo generado por el seeder. "
        "Tenés actividades pendientes de entrega en MAT-101. "
        "Por favor revisá el campus virtual."
    )

    for _nombre, _apellidos, email_plain, _comision, _regional in _STUDENTS:
        db.add(
            Comunicacion(
                tenant_id=tid,
                enviado_por=admin.id,
                materia_id=mat101.id,
                destinatario=encrypt_pii(email_plain),
                asunto=_DEMO_ASUNTO,
                cuerpo=_cuerpo,
                estado="Pendiente",
                lote_id=lote_id,
                aprobado=False,
            )
        )


# ---------------------------------------------------------------------------
# Coloquios (Evaluacion + candidatos + reservas + resultados)
# ---------------------------------------------------------------------------


async def _seed_coloquios(db: AsyncSession, tid) -> None:
    """Crea 1 Evaluacion (coloquio MAT-101) con candidatos, reservas y resultados."""
    mat_result = await db.execute(
        select(Materia).where(
            Materia.tenant_id == tid,
            Materia.codigo == "MAT-101",
            Materia.deleted_at.is_(None),
        )
    )
    mat101 = mat_result.scalar_one_or_none()
    if mat101 is None:
        return

    cohorte_result = await db.execute(
        select(Cohorte).where(
            Cohorte.tenant_id == tid,
            Cohorte.nombre == "Cohorte 2026",
            Cohorte.deleted_at.is_(None),
        )
    )
    cohorte = cohorte_result.scalar_one_or_none()
    if cohorte is None:
        return

    # Evaluacion (idempotent by materia+cohorte+instancia)
    _instancia = "Primer Coloquio 2026"
    eval_check = await db.execute(
        select(Evaluacion).where(
            Evaluacion.tenant_id == tid,
            Evaluacion.materia_id == mat101.id,
            Evaluacion.cohorte_id == cohorte.id,
            Evaluacion.instancia == _instancia,
            Evaluacion.deleted_at.is_(None),
        )
    )
    evaluacion = eval_check.scalar_one_or_none()
    if evaluacion is None:
        evaluacion = Evaluacion(
            tenant_id=tid,
            materia_id=mat101.id,
            cohorte_id=cohorte.id,
            tipo=TipoEvaluacion.COLOQUIO.value,
            instancia=_instancia,
            dias_disponibles=3,
            cupo_por_dia=10,
        )
        db.add(evaluacion)
        await db.flush()  # need evaluacion.id

    # Fetch the seeded alumnos for comisión A — use VersionPadron seed entries
    version_result = await db.execute(
        select(VersionPadron).where(
            VersionPadron.tenant_id == tid,
            VersionPadron.materia_id == mat101.id,
            VersionPadron.origen == "seed",
            VersionPadron.deleted_at.is_(None),
        )
    )
    version = version_result.scalar_one_or_none()
    if version is None:
        return

    entries_result = await db.execute(
        select(EntradaPadron).where(
            EntradaPadron.tenant_id == tid,
            EntradaPadron.version_id == version.id,
            EntradaPadron.deleted_at.is_(None),
        )
    )
    entries = list(entries_result.scalars().all())
    if not entries:
        return

    # Need real Usuario ids — fetch admin and docentes to use as "alumno_id"
    # since EntradaPadron.usuario_id is None in seed (unlinked). Use docentes instead
    # so FK constraint to usuarios.id is satisfied.
    docente_hashes = [
        hash_email_for_lookup("maria.gonzalez@demo.edu"),
        hash_email_for_lookup("carlos.lopez@demo.edu"),
        hash_email_for_lookup("laura.ruiz@demo.edu"),
    ]
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

    docentes_result = await db.execute(
        select(Usuario).where(
            Usuario.tenant_id == tid,
            Usuario.email_hash.in_(docente_hashes),
            Usuario.deleted_at.is_(None),
        )
    )
    docentes = list(docentes_result.scalars().all())

    # Compose the candidate pool: admin + up to 3 docentes = 4 candidates
    candidate_users: list[Usuario] = []
    if admin is not None:
        candidate_users.append(admin)
    candidate_users.extend(docentes[:3])
    candidate_users = candidate_users[:4]  # cap at 4

    if not candidate_users:
        return

    # EvaluacionCandidato (idempotent: EvaluacionCandidato has no BaseModelMixin,
    # use composite PK check)
    for usuario in candidate_users:
        cand_check = await db.execute(
            select(EvaluacionCandidato).where(
                EvaluacionCandidato.evaluacion_id == evaluacion.id,
                EvaluacionCandidato.alumno_id == usuario.id,
            )
        )
        if cand_check.scalar_one_or_none() is None:
            db.add(
                EvaluacionCandidato(
                    evaluacion_id=evaluacion.id,
                    alumno_id=usuario.id,
                )
            )
    await db.flush()

    # ReservaEvaluacion — first 2 candidates (idempotent by evaluacion+alumno)
    fecha_base = datetime(2026, 6, 25, 10, 0, tzinfo=timezone.utc)
    for idx, usuario in enumerate(candidate_users[:2]):
        reserva_check = await db.execute(
            select(ReservaEvaluacion.id).where(
                ReservaEvaluacion.tenant_id == tid,
                ReservaEvaluacion.evaluacion_id == evaluacion.id,
                ReservaEvaluacion.alumno_id == usuario.id,
                ReservaEvaluacion.deleted_at.is_(None),
            )
        )
        if reserva_check.scalar_one_or_none() is None:
            db.add(
                ReservaEvaluacion(
                    tenant_id=tid,
                    evaluacion_id=evaluacion.id,
                    alumno_id=usuario.id,
                    fecha_hora=fecha_base + timedelta(hours=idx),
                    estado=EstadoReserva.ACTIVA.value,
                )
            )

    # ResultadoEvaluacion — same 2 candidates (idempotent by evaluacion+alumno)
    _notas = ["8", "Aprobado"]
    for idx, usuario in enumerate(candidate_users[:2]):
        resultado_check = await db.execute(
            select(ResultadoEvaluacion.id).where(
                ResultadoEvaluacion.tenant_id == tid,
                ResultadoEvaluacion.evaluacion_id == evaluacion.id,
                ResultadoEvaluacion.alumno_id == usuario.id,
                ResultadoEvaluacion.deleted_at.is_(None),
            )
        )
        if resultado_check.scalar_one_or_none() is None:
            db.add(
                ResultadoEvaluacion(
                    tenant_id=tid,
                    evaluacion_id=evaluacion.id,
                    alumno_id=usuario.id,
                    nota_final=_notas[idx],
                )
            )
