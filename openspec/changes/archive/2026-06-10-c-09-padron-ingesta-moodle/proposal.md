## Why

Sin padrón no hay análisis: todos los módulos que detectan atrasados, generan comunicaciones y calculan métricas dependen de saber quiénes son los alumnos de cada materia × cohorte. C-09 establece la capa de ingesta — versionada, auditada e integrada con Moodle WS — que alimenta el resto del camino crítico (C-10 → C-11 → C-12).

## What Changes

- Nuevo modelo de datos: `VersionPadron` + `EntradaPadron` con soporte de versionado (activar nueva versión desactiva la anterior).
- Importación de padrón desde archivo `.xlsx` / `.csv` con columnas normalizadas y vista previa pre-confirmación.
- Cliente `integrations/moodle_ws.py`: sync de usuarios y actividades vía Moodle Web Services; sync nocturna + on-demand.
- Endpoint para vaciar datos de padrón de una materia (scope-isolated, RN-04).
- Audit `PADRON_CARGAR` en toda operación de ingesta.
- Migración `006: version_padron, entrada_padron`.

## Capabilities

### New Capabilities

- `padron-versionado`: gestión de versiones del padrón por materia × cohorte; solo una versión activa en simultáneo; activar nueva desactiva la anterior (sin borrado físico).
- `padron-import`: importación de padrón desde archivo (xlsx/csv), validación de columnas, vista previa y confirmación.
- `moodle-ws-client`: cliente de integración con Moodle Web Services; sync on-demand y nocturna; manejo de errores → 502 con reintento.

### Modified Capabilities

_(ninguna — no hay specs previas de padrón ni de Moodle WS)_

## Impact

- **Modelos nuevos**: `VersionPadron`, `EntradaPadron` (migración 006).
- **Endpoints nuevos**: `POST /api/padron/import`, `GET /api/padron/preview`, `POST /api/padron/activate/{version_id}`, `DELETE /api/padron/{materia_id}` (vaciar scope-isolated), `POST /api/padron/moodle-sync`.
- **Módulo nuevo**: `integrations/moodle_ws.py` + scheduler de sync nocturna.
- **Permisos requeridos**: `padron:cargar` (PROFESOR sobre sus materias, COORDINADOR global).
- **Dependencias externas**: Moodle Web Services API (configurable por tenant; fallback a import manual si no está disponible).
- **Siguientes changes habilitados**: C-10 `calificaciones-y-umbral` (consume `EntradaPadron`).
