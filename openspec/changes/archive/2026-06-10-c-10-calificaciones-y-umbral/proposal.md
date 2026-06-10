## Why

Los datos de padrón ya están en el sistema (C-09), pero no hay forma de asociar notas a los alumnos ni de determinar si están aprobados o atrasados. Este change introduce el núcleo del análisis académico: importar calificaciones desde el LMS, configurar umbrales por materia y derivar el estado de aprobación por alumno/actividad — habilitando el flujo central del PROFESOR (FL-02) y desbloqueando C-11 (análisis de atrasados) y C-12 (comunicaciones).

## What Changes

- **Nuevo modelo `Calificacion`**: almacena nota numérica y/o textual por (entrada_padron, materia, actividad). Campo `aprobado` derivado según umbral o conjunto aprobatorio.
- **Nuevo modelo `UmbralMateria`**: configuración de umbral de aprobación por asignación docente (defecto 60%). Incluye lista de valores textuales aprobatorios.
- **Migración 008**: tablas `calificacion` y `umbral_materia` con índices y FK.
- **Parser de archivo LMS** (F1.1): detecta columnas `*(Real)` (RN-01) y columnas textuales (RN-02). Genera vista previa de actividades/alumnos detectados. El docente selecciona qué actividades incluir.
- **Parser de reporte de finalización** (F1.2): detecta actividades finalizadas sin nota textual (RN-07, RN-08).
- **Endpoints REST**:
  - `POST /api/v1/calificaciones/preview` — vista previa sin persistir
  - `POST /api/v1/calificaciones/import` — confirmar importación
  - `POST /api/v1/calificaciones/import-finalizacion` — reporte de finalización
  - `DELETE /api/v1/calificaciones/{materia_id}` — vaciar datos propios (RN-04)
  - `GET /api/v1/umbral/{materia_id}` — obtener umbral vigente
  - `PUT /api/v1/umbral/{materia_id}` — configurar umbral (F2.1)
- **Permisos**: `calificaciones:importar`, `calificaciones:ver`, `calificaciones:vaciar`.
- **Audit**: evento `CALIFICACIONES_IMPORTAR` al confirmar importación.
- **Vaciar scope-isolated** (RN-04): elimina solo los datos del usuario en esa materia.

## Capabilities

### New Capabilities

- `calificaciones-importacion`: importar calificaciones desde archivo LMS, vista previa de actividades/alumnos, selección de actividades a incluir, confirmación y persistencia. Incluye parser para escalas numéricas (RN-01) y textuales (RN-02).
- `calificaciones-finalizacion`: importar reporte de finalización de actividades del LMS para detectar entregas sin calificar (RN-07, RN-08).
- `umbral-aprobacion`: configurar y consultar el umbral de aprobación por materia y asignación docente. Defecto 60% (RN-03). Scope aislado por docente (RN-04).

### Modified Capabilities

<!-- No existen specs previas relacionadas con calificaciones. -->

## Impact

- **Backend**: nuevos módulos `app/models/calificacion.py`, `app/models/umbral_materia.py`, `app/repositories/calificacion_repository.py`, `app/repositories/umbral_repository.py`, `app/services/calificacion_service.py`, `app/api/v1/routers/calificaciones.py`, `app/api/v1/routers/umbral.py`, utilidad `app/utils/lms_parser.py`.
- **DB**: migración `alembic/versions/008_calificacion_umbral.py`.
- **main.py**: registro de routers nuevos.
- **Dependencias**: `C-09` (EntradaPadron, VersionPadron ya existen) — C-10 no afecta el padrón, solo lo referencia.
- **Desbloquea**: `C-11` (análisis de atrasados usa `Calificacion` + `UmbralMateria`) y `C-12` (comunicaciones consume el análisis).
