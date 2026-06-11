## Context

El sistema ya tiene un worker async (`workers/main.py`) con el patrón de loop periódico establecido en C-09. La integración con N8N está definida en la arquitectura (`n8n_client.py`) pero no implementada. El módulo de analisis (C-11) ya expone `alumno_email` descifrado en los resultados, lo que permite poblar `destinatario` al encolar.

El modelo `Comunicacion` (E-21) define destinatario como `[cifrado]`. La aprobación de envíos masivos es configurable por tenant (`requiere_aprobacion_comunicaciones` en el modelo `Tenant`).

## Goals / Non-Goals

**Goals:**
- Ciclo de vida completo de mensajes salientes: preview → encolar → aprobar → despachar → trackear.
- Worker asíncrono integrado al proceso existente (sin nueva dependencia de cola externa tipo Redis/RabbitMQ).
- Integración N8N como canal de despacho real; fallback con log de error en caso de falla de webhook.
- Destinatario cifrado AES-256 en reposo; descifrado solo al momento del envío en el worker.

**Non-Goals:**
- No implementar SMTP directo — el despacho real es responsabilidad de N8N.
- No implementar mensajería interna entre usuarios del sistema (eso es C-20).
- No implementar reintentos automáticos con backoff exponencial (puede venir en un refactor posterior).

## Decisions

### D-01 — Worker como loop asyncio, sin Redis/Celery
**Decisión**: el worker de comunicaciones sigue el patrón de `padron_sync_worker.py` — un loop `asyncio` que duerme entre ciclos (intervalo configurable, default 30 segundos). Se integra en `workers/main.py` via `asyncio.gather`.  
**Alternativa descartada**: ARQ (async job queue con Redis). Se descartó para no introducir Redis como nueva dependencia en el MVP. Si el volumen de comunicaciones lo requiere en el futuro, la migración es mecánica.  
**Trade-off**: sin cola persistente entre reinicios — mensajes en estado `Enviando` al reiniciar el worker quedan colgados. Mitigación: al arrancar, el worker resetea a `Pendiente` los mensajes que quedaron en `Enviando` hace más de N minutos (configurable).

### D-02 — N8N como canal de despacho
**Decisión**: el worker llama a N8N via `POST {N8N_WEBHOOK_URL}` con payload JSON `{destinatario, asunto, cuerpo}`. N8N gestiona el envío real.  
**Rationale**: ADR-003 define N8N como integración. El `n8n_client.py` es una capa delgada (HTTP POST async) que mockea fácilmente en tests.  
**Fallo N8N**: si el webhook devuelve error o timeout → estado `Error`, se loguea el motivo. No hay reintento automático en MVP (tarea manual del operador).

### D-03 — Aprobación configurable via flag en Tenant
**Decisión**: `Tenant.requiere_aprobacion_comunicaciones: bool` (default `False`). El service verifica este flag en cada encolado. Si `True`, los mensajes quedan en `Pendiente` hasta aprobación explícita; si `False`, el worker los procesa directamente.  
**Alternativa descartada**: configuración por materia o por rol. Se descartó porque la KB dice "configurable por tenant" (§5.2 de arquitectura).

### D-04 — Cifrado en reposo del destinatario
**Decisión**: `destinatario` se cifra con el helper AES-256 existente (`core/encryption.py`) al persistir. El worker descifra en memoria antes de enviar a N8N — nunca aparece descifrado en logs ni en respuestas de API.  
**Rationale**: regla dura #12 — PII cifrada en reposo.

### D-05 — lote_id agrupa envíos masivos
**Decisión**: el encolado masivo genera un UUID `lote_id` para todas las filas del lote. El encolado individual también genera un `lote_id` (lote de 1 elemento).  
**Rationale**: simplifica el tracking (un GET por lote devuelve el estado de todos los mensajes del lote) y la aprobación (se puede aprobar o cancelar todo el lote en una operación).

### D-06 — Campo `requiere_aprobacion` en Tenant
**Decisión**: agregar `requiere_aprobacion_comunicaciones: bool = False` al modelo `Tenant` existente. No requiere migración de datos nueva si se usa `server_default=False`. Solo requiere `ALTER TABLE tenant ADD COLUMN`.  
**Alternativa**: tabla de configuración por tenant. Descartada por sobre-ingeniería para una sola configuración.

## Risks / Trade-offs

- **[Riesgo] Mensajes en estado `Enviando` al reiniciar worker** → Mitigación: D-01, reset al arranque si `Enviando` hace más de `COMUNICACION_STALE_THRESHOLD_MINUTES` (default 10 min).
- **[Riesgo] N8N no disponible → todos los envíos fallan** → Mitigación: log estructurado con `lote_id`, `comunicacion_id`, motivo. El operador puede reintentar con endpoint `POST /api/comunicaciones/{id}/retry` (cambia de `Error` a `Pendiente`).
- **[Trade-off] Sin Redis/Celery** → volumen de ~1000 emails/lote es manejable con asyncio. Si se necesitan >10k emails/lote, la arquitectura requerirá upgrade.

## Migration Plan

1. `alembic revision --autogenerate -m "comunicacion"` — genera migración con tabla `comunicacion`.
2. Agregar columna `requiere_aprobacion_comunicaciones` al modelo `Tenant` con `server_default='false'` (sin ruptura de datos existentes).
3. Verificar permisos `comunicacion:enviar` y `comunicacion:aprobar` en seed RBAC.
4. Agregar `N8N_WEBHOOK_URL` a `.env.example` y docs de deploy.
5. Worker: el nuevo loop se suma al `asyncio.gather` existente sin downtime adicional.

## Open Questions

- ¿La variable `requiere_aprobacion_comunicaciones` va en el modelo `Tenant` o en una tabla `TenantConfig`? Decisión provisional: en `Tenant` directamente (menor complejidad, única configuración por ahora).
- ¿Cuántos reintentos máximos antes de marcar como `Error` definitivo? Decisión provisional: 0 reintentos automáticos en MVP (manual via endpoint retry). Se puede configurar en una iteración futura.
