## Context

El módulo de coloquios cubre el flujo completo de evaluaciones formales (FL-07): un COORDINADOR crea una convocatoria con días disponibles y cupos, importa candidatos habilitados, los alumnos reservan turno, y el sistema registra los resultados finales. Actualmente no existe ningún modelo ni endpoint para esto; todo se maneja fuera del sistema.

Las entidades definidas en E14 del modelo de datos son: `Evaluacion`, `ReservaEvaluacion` y `ResultadoEvaluacion`. C-14 las implementa completas.

Depende de C-07 (Usuario, Asignacion) y C-04 (RBAC). No hay dependencias de calificaciones (C-10/C-11).

## Goals / Non-Goals

**Goals:**
- Implementar `Evaluacion`, `ReservaEvaluacion`, `ResultadoEvaluacion` con migración Alembic.
- API REST `/api/coloquios/*` con guards RBAC (`coloquios:gestionar`, `coloquios:reservar`, `coloquios:ver`).
- Cupo por día con validación atómica: sin cupo disponible → 409.
- Panel de métricas globales (F7.1) y agenda consolidada por coordinación (F7.5).
- Multi-tenant row-level en todas las entidades.

**Non-Goals:**
- Integración con Moodle para sincronizar resultados de coloquio (fuera de alcance MVP).
- Notificaciones automáticas de confirmación de reserva (depende de C-12, se puede encolar manualmente).
- Gestión de fechas académicas (FechaAcademica — eso es C-17).
- Lógica de "alumno habilitado" basada en calificaciones previas (la habilitación se importa manualmente).

## Decisions

**D1 — Cupos por día en Evaluacion, no en entidad separada**

`Evaluacion` tiene `cupo_por_dia: int`. El cupo disponible para un día se calcula como `cupo_por_dia - count(ReservaEvaluacion WHERE fecha_hora::date = dia AND estado = Activa)`. No se crea una entidad `DiaColoquio` separada.

*Alternativa rechazada*: entidad `DiaColoquio` con cupo propio. Más flexible pero sobre-ingeniería para el MVP: los cupos son iguales por día. Si en el futuro se necesitan cupos heterogéneos por día, se agrega la entidad.

**D2 — Candidatos como relación directa a Usuario (no a EntradaPadron)**

`ReservaEvaluacion.alumno_id` apunta a `Usuario`. La importación de candidatos (F7.2) crea entradas en `evaluacion_candidato` (tabla asociativa) con el `usuario_id` de alumnos habilitados. Solo alumnos en esa lista pueden reservar.

*Motivo*: el flujo de reserva requiere que el alumno esté autenticado (necesita una cuenta). Los alumnos sin `usuario_id` en el padrón no pueden reservar por self-service; el coordinador puede registrarles el resultado directamente.

**D3 — Validación de cupo con SELECT FOR UPDATE**

Al crear una reserva, el repository hace `SELECT COUNT(*) FROM reserva_evaluacion WHERE evaluacion_id = X AND fecha_hora::date = fecha AND estado = 'Activa' FOR UPDATE` antes del INSERT. Esto previene race conditions sin necesidad de locks de aplicación ni Redis.

**D4 — Nota final como texto libre en ResultadoEvaluacion**

`nota_final: str` sin derivación de `aprobado`. El sistema registra lo que el docente ingresa ("Aprobado", "7", "Desaprobado"). No hay umbral asociado — los coloquios tienen semántica propia definida por cada institución.

**D5 — Permisos nuevos en migración 010**

Se agregan a la tabla `permiso` y se asocian en `rol_permiso`:
- `coloquios:gestionar` → COORDINADOR, ADMIN
- `coloquios:reservar` → ALUMNO  
- `coloquios:ver` → TUTOR, PROFESOR, COORDINADOR, ADMIN

## Risks / Trade-offs

[Race condition en cupo] → Mitigado por D3 (SELECT FOR UPDATE). Cubre concurrencia a nivel DB. Si en el futuro el tráfico es muy alto se puede agregar un índice funcional sobre el conteo.

[alumno sin cuenta no puede reservar] → Documentado en D2. El coordinador puede registrar el resultado igualmente. El flujo self-service requiere cuenta activa.

[cupos homogéneos por día] → Si la institución necesita cupos distintos por día (D1), la tabla `evaluacion_candidato` no lo cubre. Mitigación: diseño extensible; se puede agregar `DiaColoquio` en un change posterior sin breaking changes.

## Migration Plan

1. `010_evaluaciones.py`: crear `evaluacion`, `evaluacion_candidato`, `reserva_evaluacion`, `resultado_evaluacion`.
2. Seed RBAC: INSERT de 3 permisos nuevos + asociaciones por rol en `rol_permiso`.
3. Sin rollback destructivo: las tablas son nuevas, no afectan tablas existentes.
4. Deploy: migrar → iniciar API → permisos activos inmediatamente.

## Open Questions

Ninguna. El dominio está completamente definido en E14, F7.1–F7.5 y FL-07.
