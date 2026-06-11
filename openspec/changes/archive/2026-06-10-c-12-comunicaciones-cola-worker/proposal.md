## Why

C-11 expone la lista de alumnos atrasados pero no hay manera de contactarlos desde el sistema. C-12 cierra el flujo central del PROFESOR: seleccionar atrasados → previsualizar mensaje → encolar → despachar. Sin este change, el sistema puede analizar pero no actuar. Es el último eslabón del camino crítico `importar → analizar → comunicar` y desbloquea C-22 (frontend académico-docente).

## What Changes

- **Modelo `Comunicacion`** (E-21): tabla con estados (`Pendiente → Enviando → Enviado | Error | Cancelado`), `lote_id` para agrupación de envíos masivos, `destinatario` AES-256 cifrado, plantilla con variables de sustitución (RN-15).
- **Migración de schema**: `Migración 0NN: comunicacion`.
- **Preview obligatorio** (F3.1, RN-16): endpoint que renderiza el mensaje resuelto por alumno antes de encolar; sin persistencia.
- **Encolado individual y masivo** (F3.2): `POST /api/comunicaciones/lote` crea registros en estado `Pendiente` con `lote_id` compartido; `comunicacion:enviar`.
- **Aprobación humana configurable por tenant** (F3.3, RN-17): si el tenant tiene `requiere_aprobacion_comunicaciones = True`, los lotes pasan por `comunicacion:aprobar` antes de que el worker los procese. Aprobación por lote o individual.
- **Cancelación** de mensajes en estado `Pendiente`.
- **Worker asíncrono de despacho**: integrado en `workers/main.py`; poll de DB + despacho vía N8N webhook (`integrations/n8n_client.py`). Estados post-despacho: `Enviado` o `Error`.
- **Audit** `COMUNICACION_ENVIAR` al encolar el lote; `COMUNICACION_APROBAR` al aprobar.
- **Panel de estado**: `GET /api/comunicaciones/lote/{lote_id}/estado` para tracking en tiempo real del lote.

## Capabilities

### New Capabilities
- `comunicaciones-modelo`: Modelo `Comunicacion` con máquina de estados completa (RN-15), `lote_id`, `destinatario` cifrado AES-256, plantillas con variables de sustitución. Incluye migración.
- `comunicaciones-api`: Endpoints de preview, encolado (individual y masivo), aprobación/rechazo por lote o individual, cancelación y consulta de estado de lote. Guards `comunicacion:enviar` y `comunicacion:aprobar`.
- `comunicaciones-worker`: Worker asíncrono de despacho integrado al loop existente (`workers/main.py`). Integración con N8N via `integrations/n8n_client.py` (nuevo). Transiciones de estado Pendiente→Enviando→Enviado/Error. Retry configurable en Error.

### Modified Capabilities
- `analisis-atrasados`: Agrega el campo `alumno_email` descifrado en la respuesta de atrasados (necesario para poblar el destinatario de las comunicaciones). No cambia la lógica de detección, solo expone el email para que el frontend lo incluya al crear el lote.

## Impact

- **Nueva tabla**: `comunicacion` (Migración 0NN). Sin cambios en tablas existentes.
- **Nuevos archivos**: `backend/app/models/comunicacion.py`, `backend/app/repositories/comunicacion_repository.py`, `backend/app/services/comunicacion_service.py`, `backend/app/api/v1/routers/comunicaciones.py`, `backend/app/schemas/comunicacion.py`, `backend/app/workers/comunicacion_worker.py`, `backend/app/integrations/n8n_client.py`.
- **Modificados**: `backend/app/workers/main.py` (agrega loop de comunicaciones), `backend/app/models/__init__.py`.
- **Permisos nuevos**: `comunicacion:enviar` y `comunicacion:aprobar` deben estar en seed de RBAC. Verificar presencia.
- **Variable de entorno nueva**: `N8N_WEBHOOK_URL` (ya mencionada en §9 de ARQUITECTURA.md).
- **Governance**: ALTO — toca cifrado de PII, worker de producción e integración externa.
- **Desbloquea**: C-22 `frontend-academico-docente` (consume este módulo en el flujo PROFESOR).
