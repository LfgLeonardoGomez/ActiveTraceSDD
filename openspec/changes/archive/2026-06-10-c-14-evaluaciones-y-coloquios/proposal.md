## Why

El sistema gestiona calificaciones y comunicaciones de alumnos pero no tiene ningún mecanismo para organizar las instancias de evaluación formal (coloquios, parciales, recuperatorios): crear convocatorias con cupos, habilitar reservas de turno por alumno, ni registrar resultados consolidados. Sin C-14, los coordinadores y profesores gestionan esto fuera de la plataforma (planillas externas, email), rompiendo la trazabilidad.

## What Changes

- Nuevo modelo `Evaluacion` (convocatoria: materia × cohorte × tipo × instancia, dias_disponibles, cupos por día).
- Nuevo modelo `ReservaEvaluacion` (alumno reserva un turno con fecha_hora; estado Activa/Cancelada; sin cupo disponible → rechazo).
- Nuevo modelo `ResultadoEvaluacion` (nota final cualitativa o numérica por alumno × evaluación).
- API REST `/api/coloquios/*`:
  - Crear convocatoria (COORDINADOR/ADMIN) con carga de candidatos.
  - Listado de convocatorias con métricas operativas (convocados/reservas/cupos libres).
  - Reserva de turno por ALUMNO en día disponible con cupo.
  - Cancelar reserva.
  - Registro de resultado por alumno.
  - Panel de métricas globales (F7.1).
  - Administración global (F7.5): agenda consolidada de reservas, resultados por convocatoria.
- `Migración 010: evaluacion, reserva_evaluacion, resultado_evaluacion`.

## Capabilities

### New Capabilities

- `evaluaciones-convocatorias`: Creación y gestión de convocatorias de evaluación (materia, instancia, días disponibles, cupos). Incluye importar padrón de candidatos habilitados y listado con métricas operativas (F7.2, F7.3, F7.4, F7.5).
- `evaluaciones-reservas`: Reserva de turno por ALUMNO con validación de cupo disponible; cancelación. Control de estado Activa/Cancelada (F7, FL-07 pasos 4-5).
- `evaluaciones-resultados`: Registro de resultado final por alumno × evaluación (nota cualitativa o numérica); registro académico consolidado (F7.5, FL-07 paso 7).
- `evaluaciones-metricas`: Panel de métricas globales: total de alumnos cargados, instancias activas, reservas activas, notas registradas (F7.1). Vista de agenda consolidada por coordinación (FL-07 paso 6).

### Modified Capabilities

## Impact

- **Nuevos modelos**: `Evaluacion`, `ReservaEvaluacion`, `ResultadoEvaluacion`.
- **Migración Alembic**: `010_evaluaciones.py` — 3 tablas nuevas.
- **Nuevos endpoints**: `/api/coloquios/*` (~10 endpoints).
- **Permisos RBAC**: `coloquios:gestionar` (COORDINADOR, ADMIN), `coloquios:reservar` (ALUMNO), `coloquios:ver` (TUTOR, PROFESOR).
- **Dependencias KB**: E14 (modelo), F7.1–F7.5 (funcionalidades), FL-07 (flujo completo).
- **Sin breaking changes** en módulos existentes.
