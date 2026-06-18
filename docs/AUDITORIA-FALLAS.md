# Auditoría de Fallas, Inconsistencias y Roturas — activia-trace

> **Fecha**: 2026-06-17
> **Alcance**: backend (FastAPI) + frontend (React) + consistencia KB/docs vs código.
> **Método**: auditoría adversarial por área (seguridad, dominio, frontend, consistencia documental). Cada hallazgo cita evidencia `archivo:línea`. Los hallazgos marcados con **✓ verificado** fueron reproducidos manualmente; el resto proviene de la auditoría con evidencia concreta de código.
> **Nota de honestidad**: un hallazgo reportado inicialmente como crítico (`HTTP_422_UNPROCESSABLE_CONTENT` inexistente) resultó **FALSO** tras verificación y fue descartado. Ver §6.

---

## Resumen ejecutivo

| Severidad | Roturas (runtime) | Seguridad | Inconsistencias doc/código | Calidad/deuda | Total |
|-----------|:--:|:--:|:--:|:--:|:--:|
| **CRÍTICO** | 4 | 1 | 2 | 0 | 7 |
| **ALTO** | 14 | 2 | 5 | 1 | 22 |
| **MEDIO** | 6 | 2 | 5 | 2 | 15 |
| **BAJO** | 3 | 0 | 3 | 2 | 8 |

**Lectura rápida**: el roadmap está 100% implementado (C-01…C-24 archivados), pero hay **roturas funcionales reales** que impiden operar tres flujos completos (login en producción, comunicaciones, sincronización de padrón) y una **capa de integración frontend-backend desalineada** por prefijos de API inconsistentes.

---

## 1. ROTURAS — el sistema no funciona en runtime

### R-01 · CRÍTICO · Login y recuperación de contraseña rotos en producción ✓ verificado
- **Evidencia**: `backend/app/api/v1/routers/auth.py:132` y `:247` ejecutan `select(Usuario).where(Usuario.email == body.email, ...)`.
- **Problema**: la columna `email` se persiste **cifrada AES-256-GCM** (no determinística) vía `UsuarioRepository._encrypt_pii_fields`. Comparar el email en texto plano contra el ciphertext **nunca matchea** → todo login y todo forgot-password devuelven 401/"no encontrado" en producción.
- **Por qué los tests no lo detectan**: `tests/test_auth.py` crea usuarios con `Usuario(email=...)` directo, salteando el repositorio y el cifrado, validando un escenario imposible.
- **Fix**: usar `UsuarioRepository.get_by_email_hash()` (HMAC-SHA256 determinístico, ya existe) en lugar de la comparación cruda; corregir los fixtures de test para pasar por el repositorio.

### R-02 · CRÍTICO · Renderizado de plantillas de comunicación 100% roto ✓ verificado
- **Evidencia**: `backend/app/services/comunicacion_service.py:37,103,111`.
- **Problema**: las variables documentadas (`alumno.nombre`, `alumno.email`) contienen un punto. `string.Template` solo acepta identificadores `[_a-z][_a-z0-9]*`. `string.Template("${alumno.nombre}").substitute(...)` lanza **`ValueError: Invalid placeholder`** (reproducido). Toda preview/encolado con la sintaxis documentada devuelve 422.
- **Fix**: usar claves sin punto (`alumno_nombre`) o reemplazar `string.Template` por un render que soporte la notación con punto.

### R-03 · CRÍTICO · El worker de sincronización de padrón nunca sincroniza ✓ verificado
- **Evidencia**: `backend/app/workers/main.py:27-30` — `await worker.run_once(tenants=[], sync_configs=[])` con **listas vacías** y comentario "la query se agrega cuando C-06 exponga el modelo Tenant con moodle_url".
- **Problema**: el loop nocturno itera sobre una lista vacía → no-op permanente. Además el modelo `Tenant` (`backend/app/models/tenant.py`) **no tiene** campos `moodle_url` / `moodle_token`, por lo que la query de tenants activos no puede construirse tal como está.
- **Fix**: agregar `moodle_url`/`moodle_token` (cifrado) al `Tenant`, implementar la query de tenants activos y poblar `sync_configs`.

### R-04 · CRÍTICO · Desalineación sistémica de prefijos API frontend ↔ backend ✓ verificado
- **Causa raíz**: el backend usa prefijos **inconsistentes**. Conviven `/api/v1/...` (admin, usuarios, equipos, encuentros, calificaciones, padron, perfil, inbox, guardias, asignaciones, umbral, roles) y `/api/...` sin `v1` (auth, analisis, comunicaciones, coloquios, avisos, tareas, programas, auditoria, fechas-academicas). Verificado en `backend/app/api/v1/routers/*.py` (cláusulas `prefix=`).
- **Consecuencia**: el frontend asume el prefijo equivocado y produce **404/405 en producción** en numerosas pantallas. Mismatches confirmados:

  | Pantalla / acción | Frontend llama | Backend expone | Estado |
  |---|---|---|---|
  | Confirmar aviso | `POST /api/v1/avisos/{id}/ack` | `POST /api/avisos/{id}/confirmar` ✓ | 404 (prefijo + path) |
  | Monitor coordinación | `/api/v1/analisis/monitor/general` | `/api/analisis/...` | 404 |
  | Coloquios (todo) | `/api/v1/coloquios/*` | `/api/coloquios/*` | 404 |
  | Tareas (todo) | `/api/v1/tareas/*` | `/api/tareas/*` | 404 |
  | Vaciar calificaciones | `POST /api/v1/calificaciones/vaciar` | `DELETE /api/v1/calificaciones/{materia_id}` | 405/404 |
  | Aprobar/cancelar lote | `.../lote/{id}/approve`·`/cancel` | `.../lote/{id}/aprobar`·`/cancelar` | 404 |
  | Admin estructura/usuarios | `/api/admin/...`, `PATCH usuarios` | `/api/v1/admin/...`, `PUT usuarios` | 404/405 |
  | Salarios / facturas / liquidaciones | `/api/liquidaciones/*`, `/api/facturas` | `/api/v1/liquidaciones/*`, `/api/v1/facturas` | 404 |
  | Encuentros guardias | `/api/v1/encuentros/guardias` | router separado `/api/v1/guardias` | 404 |
  | Coordinación estructura | `/api/v1/estructura/*` | `/api/v1/admin/*`, `/api/programas` | 404 |

  Referencias frontend: `features/coordinacion/services/{avisos,monitor,estructura,tareas,encuentros}.api.ts`, `features/comisiones/services/comisiones.api.ts`, `features/finanzas/services/{salarios,facturas,liquidaciones}.api.ts`, `features/admin/services/{estructura,usuarios}.api.ts`, `features/coordinacion/services/coloquios.api.ts`.
- **Fix**: unificar el contrato de prefijos (recomendado: **todo bajo `/api/v1`**) y alinear todos los `*.api.ts`. Idealmente, generar un cliente tipado desde el OpenAPI del backend para que esto no vuelva a divergir.

### R-05 · ALTO · `detectar_sin_corregir` cruza por actividad global, no por alumno
- **Evidencia**: `backend/app/services/finalizacion_service.py:72-83` — `calificados_key` se construye pero nunca se usa; el filtro real compara solo `fila.actividad`.
- **Problema**: si **un** alumno tiene nota en "TP1", **todos** los demás quedan excluidos de "sin corregir" para esa actividad → falsos negativos masivos. El cruce correcto es por `(alumno, actividad)`.

### R-06 · ALTO · `periodo` sin validación → 500 no capturado
- **Evidencia**: `backend/app/modules/liquidaciones/services/liquidacion_calc_service.py:297` y `repositories/salario_base_repo.py:31` — `int(periodo[:4])`, `int(periodo[5:7])` sin validar formato `AAAA-MM`.
- **Problema**: un `periodo` mal formado (ej. `2025-AB`) lanza `ValueError` no capturado → HTTP 500 en 3 endpoints de liquidaciones.
- **Fix**: validar con `Path(..., pattern=r"^\d{4}-\d{2}$")` o `field_validator`.

### R-07 · ALTO · Log de impersonación guarda ciphertext en lugar de email legible
- **Evidencia**: `backend/app/api/v1/routers/auth.py:556` — `detalle={"target_email": target.email}` con `target` ORM crudo (email cifrado).
- **Problema**: el registro de auditoría "¿a qué usuario se impersonó?" queda ilegible. El patrón correcto (`decrypt_pii`) ya se usa en `dependencies.py:126,153`.

### R-08 · ALTO · `logger.error` en flood cuando N8N no está configurado
- **Evidencia**: `backend/app/workers/comunicacion_worker.py:59-66`, loop cada 30s en `workers/main.py`.
- **Problema**: sin `N8N_WEBHOOK_URL`, se emite un ERROR cada ciclo (~2.880/día), enmascarando errores reales. Debe ser WARNING única o gateo al inicio.

### R-09 · ALTO · Inbox (mensajería interna) sin UI
- **Evidencia**: backend `inbox.py` (`/api/v1/inbox`) completo y testeado; **no hay** página/ruta/servicio en frontend (`App.tsx` no declara `/inbox`).
- **Estado**: C-20 backend OK, frontend ausente.

### R-10 · ALTO · Perfil de usuario sin UI
- **Evidencia**: backend `perfil.py` (`PATCH /api/v1/perfil`) implementado; **no hay** página ni servicio en frontend.

### R-11 · ALTO · Rutas de coordinación sin `PermissionGuard`
- **Evidencia**: `frontend/src/App.tsx:91-127` — `/coordinacion` y subrutas (encuentros, equipos, coloquios, estructura, avisos, monitor) sin guard de permiso: cualquier usuario autenticado entra.
- **Nota**: admin y finanzas **sí** están protegidos correctamente.

### R-12 · ALTO · `/comisiones/:materiaId` sin `PermissionGuard`
- **Evidencia**: `frontend/src/App.tsx:78-89` — el guard se aplica solo en el selector de `ComisionesPage`; `ComisionDetailPage` y subrutas (umbral, notas, comunicaciones) quedan sin protección por permiso.

### R-13 · MEDIO · Race condition en cierre de liquidación
- **Evidencia**: `backend/app/modules/liquidaciones/services/liquidacion_cierre_service.py:48-49` — ventana entre `periodo_esta_cerrado()` y `bulk_create_cerradas`, sin `SELECT FOR UPDATE` ni constraint `UNIQUE(tenant_id, cohorte_id, periodo)`.
- **Riesgo**: dos cierres concurrentes del mismo período → filas duplicadas en estado `Cerrada`.

### R-14 · MEDIO · `resetear_colgados` se ejecuta en cada ciclo
- **Evidencia**: `backend/app/workers/comunicacion_worker.py:86` — un `UPDATE`+commit cada 30s; debería correr solo en startup.

### R-15 · MEDIO · `Settings()` a nivel de módulo aborta el import sin env
- **Evidencia**: `backend/app/core/encryption.py:22` (también `security.py:20`, `token_service.py:14`) — `settings = Settings()` en import. Sin `ENCRYPTION_KEY`/`SECRET_KEY`, el import falla antes de que el lifespan valide config (rompe build/tests sin env).

### R-16 · MEDIO · Descifrado silencia errores (corrupción invisible)
- **Evidencia**: `backend/app/repositories/padron_repository.py:174-179` y `usuarios.py:78` — `except Exception: pass` deja PII corrupta/ciphertext como valor visible sin alertar.

### R-17 · MEDIO · `get_pendientes_para_despacho` no filtra `aprobado`
- **Evidencia**: `backend/app/repositories/comunicacion_repository.py:236-258` — el docstring promete filtrar por `aprobado=True`, la query no lo hace. Hoy es dead code (el worker usa otro método correcto), pero es una trampa para uso futuro: despacharía mensajes no aprobados.

### R-18 · MEDIO · `_calcular_desde_snapshot` silencia JSON corrupto
- **Evidencia**: `backend/app/modules/liquidaciones/services/liquidacion_calc_service.py:93-97` — `except Exception: pass` devuelve `plus_detalle=[]` ante `detalle_plus` corrupto, ocultando plus reales del docente.

### R-19 · BAJO · Worker dispatch: `resetear_colgados` y logging — ver R-08/R-14 (consolidado).

---

## 2. FALLAS de seguridad / append-only

### S-01 · ALTO · Hard delete real de `EvaluacionCandidato` (viola append-only, regla #13)
- **Evidencia**: `backend/app/repositories/evaluacion_repository.py:141-150` — `delete(EvaluacionCandidato).where(...)` físico en `import_candidatos`. El modelo (línea 76) no hereda `BaseModelMixin` (sin `deleted_at`). Reimportar un padrón borra la historia de candidatos previos.

### S-02 · MEDIO · Query `text()` sin filtro `tenant_id` explícito (regla #9)
- **Evidencia**: `backend/app/repositories/evaluacion_repository.py:186-197` — `count_reservas_activas_en_dia` filtra solo por `evaluacion_id`; el aislamiento es indirecto vía FK. Además `FOR UPDATE` sin transacción explícita.

### S-03 · MEDIO · Hard delete de `RateLimitBucket`
- **Evidencia**: `backend/app/repositories/rate_limit_repository.py:64` — `delete(...)` físico. Es infra (no business data), por eso MEDIO, pero viola literalmente la regla #13 y elimina forensics de rate-limiting.

> **Nota positiva (verificado)**: la multi-tenancy NO está rota. El aislamiento real vive en `BaseRepository` (fail-closed: sin `tenant_id` lanza `ValueError`) y el `tenant_id` proviene de `current_user.tenant_id` (JWT, regla #8). El archivo `backend/app/core/tenancy.py` es un **stub muerto** con docstring "RESERVADO para C-02" (C-02 ya archivado) — confunde, pero no es un agujero. Conviene borrarlo o documentarlo.

---

## 3. INCONSISTENCIAS documentación vs código

### IC-01 · CRÍTICO · ADR-006: entidad `Dictado` documentada como "cerrada" pero nunca implementada ✓ verificado
- **Doc**: `docs/ARQUITECTURA.md:346` declara ADR-006 cerrada: "`Dictado` es la instancia de `Materia` en `carrera × cohorte`; calificaciones, equipos, encuentros y coloquios cuelgan del `Dictado`".
- **Código**: **no existe** ningún modelo `Dictado` (`backend/app/models/` — confirmado). Encuentros, guardias, calificaciones y padrón referencian `materias.id` directo. La migración `005_carrera_cohorte_materia.py` no crea `dictados`.
- **Impacto**: el modelo de datos real contradice un ADR marcado como cerrado, y deja **PA-01 efectivamente sin resolver** en el esquema.

### IC-02 · CRÍTICO · C-06 implementado con PA-01 y PA-07 todavía abiertas
- **Doc**: `knowledge-base/10_preguntas_abiertas.md:9,29` — PA-01 y PA-07 figuran abiertas; CLAUDE.md las marca como **bloqueantes** de C-06.
- **Código**: C-06 archivado; `backend/app/models/estructura.py:76` fija `Cohorte.carrera_id NOT NULL`, asumiendo la respuesta de PA-07 sin cierre formal. Inconsistencia de **proceso**: se codeó un dominio crítico con sus preguntas bloqueantes abiertas.

### IC-03 · ALTO · Permisos de liquidaciones no se crean por migración
- **Evidencia**: `backend/app/modules/liquidaciones/permissions.py` + `seed.py` definen `liquidaciones:configurar-salarios`, `liquidaciones:calcular`, `liquidaciones:cerrar`, `facturas:cargar`, pero el seed **no se invoca** desde ninguna migración Alembic ni desde el lifespan (`main.py:45-51`). La migración `015_c18_liquidaciones.py` no llama al seed.
- **Impacto**: en un deploy limpio (solo `alembic upgrade`), el módulo de liquidaciones queda **sin permisos RBAC funcionales**.

### IC-04 · ALTO · RN-05 contradice el modelo de padrón implementado
- **Doc**: `knowledge-base/05_reglas_de_negocio.md:22` (RN-05): "la carga reemplaza completamente el padrón anterior; **no se conserva historial**". Pero `04_modelo_de_datos.md:141-172` (E6) documenta versionado con historial — **contradicción interna de la KB**.
- **Código**: `backend/app/models/padron.py:11` + `repositories/padron_repository.py:80-116` implementan **historial versionado** (desactiva sin borrar). El código siguió E6 e ignoró RN-05.

### IC-05 · ALTO · `SlotEncuentro` diverge del modelo E9
- **Doc**: `knowledge-base/04_modelo_de_datos.md:222-244` define `asignacion_id`, `fecha_unica`, `vig_desde`, `vig_hasta`.
- **Código**: `backend/app/models/slot_encuentro.py` usa `creador_id` (FK directa a usuario) y un `vigencia` como texto libre; faltan `fecha_unica`/`vig_desde`/`vig_hasta`. Implicación: el slot se liga al usuario, no a su asignación de rol.

### IC-06 · ALTO · `Guardia` diverge del modelo E11
- **Doc**: `04_modelo_de_datos.md:271-285` — `asignacion_id` + `dia: enum` (recurrente semanal).
- **Código**: `backend/app/models/guardia.py:34-53` — `tutor_id` (FK usuario) + `fecha: Date` (puntual). Cambia la semántica de la guardia.

### IC-07 · ALTO · Permiso duplicado `evaluacion:reservar` vs `coloquios:reservar`
- **Evidencia**: seed `002_create_rbac_tables.py:140,176` crea `evaluacion:reservar` (a ALUMNO); seed `010_evaluaciones.py:230` crea `coloquios:reservar` (a ALUMNO). El router `coloquios.py:252` usa `coloquios:reservar`. El permiso `evaluacion:reservar` queda **huérfano**.

### IC-08 · MEDIO · RN-26 (datos bancarios para liquidar) sin validar
- **Evidencia**: `liquidacion_calc_service.py:193-255` genera filas sin verificar `banco`/`cbu`/`alias_cbu`. La KB (`05_reglas_de_negocio.md:183-185`) lo exige. Un docente sin CBU genera liquidación igual.

### IC-09 · MEDIO · RN-28 (token CSRF en escrituras) no implementado
- **Evidencia**: sin referencias a `csrf`/`X-CSRF-Token` en el backend. La KB (`05_reglas_de_negocio.md:194-196`) lo exige. (Mitigado en parte por JWT, pero el requisito documental no está satisfecho.)

### IC-10 · MEDIO · PA-25 (rol NEXO) figura abierta y cerrada a la vez
- **Evidencia**: `10_preguntas_abiertas.md:69-81` (abierta, prioridad ALTA) y `:247` (decisión cerrada ADR-008). El código (`002_create_rbac_tables.py:237`) crea NEXO con matriz vacía — consistente con la decisión cerrada, pero la KB se contradice.

### IC-11 · MEDIO · `estado_academico:ver` seeded pero sin endpoint
- **Evidencia**: `002_create_rbac_tables.py:139,175` asigna `estado_academico:ver` a ALUMNO, pero no hay router de estado académico del alumno. Funcionalidad documentada (objetivo ALUMNO) faltante.

### IC-12 · MEDIO · `Tarea` con campos no documentados en E12
- **Evidencia**: `backend/app/models/tarea.py:47-92` agrega `titulo`, `criterio_cierre`, `aprobada`, `devuelta`, `revisada_por`, `revisada_at`. No contradicen la KB pero `04_modelo_de_datos.md:293-312` está desactualizada.

### IC-13 · BAJO · Numeración de migraciones no coincide con CHANGES.md
- **Evidencia**: `CHANGES.md:211-214` dice "Migración 003: audit_log". En realidad C-03 (auth) usa archivo con hash `3a51a71a68ef_...` y audit_log es `004_*`. No existe `003_*`. La cadena Alembic **no está rota** (el branch intencional en `007_*` converge correctamente en `008` con `down_revision` tupla), pero la nomenclatura documentada es engañosa.

### IC-14 · BAJO · Valor `ALL` de `SalarioBase` (E17) no existe en el enum
- **Evidencia**: `04_modelo_de_datos.md:437` documenta `ALL` como rol global; no aparece en `app/modules/liquidaciones/models/enums.py`.

### IC-15 · BAJO · `Evaluacion.cupo_por_dia` no documentado en E14
- **Evidencia**: `backend/app/models/evaluacion.py:73` agrega `cupo_por_dia`; `04_modelo_de_datos.md:358-365` no lo menciona.

---

## 4. Calidad / deuda técnica

### Q-01 · ALTO · Moodle y N8N con credenciales globales (no por tenant)
- **Evidencia**: `backend/app/core/config.py:33-34` define `moodle_url`/`moodle_token` globales; `padron.py:214,231` instancia el cliente con esa config. El `padron_sync_worker.py` hace `getattr(tenant, "moodle_url", None)` que nunca existe. Multi-tenant real con Moodles distintos por institución es imposible hoy.

### Q-02 · MEDIO · Archivos backend > 500 LOC (regla #15)
- `analisis_repository.py` (754), `auth.py` (586), `evaluacion_repository.py` (533).

### Q-03 · MEDIO · Componentes frontend > 200 LOC (12 archivos)
- `EstructuraPages.tsx` (337), `ComunicacionTracking.tsx` (329), `ConvocatoriaForm.tsx` (309), `AvisoForm.tsx` (307), `ColoquiosPages.tsx` (284), `AuditoriaTable.tsx` (265), `TareaTable.tsx` (259), `SalarioGridPage.tsx` (240), `GuardiaTable.tsx` (231), `AtrasadosTable.tsx` (229), `Sidebar.tsx` (226), `EstructuraPage.tsx` (226).

### Q-04 · BAJO · `as any` y formularios sin Zod en frontend
- `ConvocatoriaForm.tsx:126` usa `as any` (única ocurrencia en `src/`). `AsignacionMasivaForm.tsx` y `ClonarEquipoForm.tsx` usan `useState` crudo sin `react-hook-form`+Zod en flujos críticos (asignación masiva, clonado de equipos).

### Q-05 · BAJO · UI de configuración Moodle por tenant ausente
- No hay pantalla para cargar `moodle_url`/`token` por institución (depende de Q-01 y R-03).

---

## 5. Variables de entorno requeridas (referencia)

**`backend/.env` — requeridas (la app no arranca sin ellas)**: `DATABASE_URL`, `SECRET_KEY` (≥32 chars), `ENCRYPTION_KEY` (=32 chars).
**`backend/.env` — operativas (default, pero necesarias para funcionar)**: `MOODLE_URL`, `MOODLE_TOKEN`, `N8N_WEBHOOK_URL`, `N8N_TIMEOUT_SECONDS`, `OTEL_ENABLED`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `REFRESH_COOKIE_SECURE`, `COMUNICACION_DISPATCH_INTERVAL_SECONDS`, `COMUNICACION_BATCH_SIZE`, `COMUNICACION_STALE_THRESHOLD_MINUTES`.
**`frontend/.env`**: `VITE_API_BASE_URL`.

---

## 6. Hallazgo descartado (transparencia)

- **`HTTP_422_UNPROCESSABLE_CONTENT` inexistente** — reportado como CRÍTICO en `analisis.py`, `coloquios.py`, `analisis_service.py`. **FALSO**: en Starlette 1.3.0 (versión instalada) el atributo **existe** (`hasattr == True`). No es una rotura. Se documenta para evitar que se "arregle" algo que funciona.

---

## 7. Plan de remediación sugerido (por prioridad)

1. **Bloqueantes de operación** (R-01, R-02, R-03, R-04): sin esto, login, comunicaciones, sync de padrón y media UI no funcionan en producción. **Empezar acá.**
2. **Seguridad/integridad** (S-01, R-07, IC-03): append-only roto, auditoría ilegible, RBAC de liquidaciones no se siembra.
3. **Correctitud de dominio** (R-05, R-06, R-13, IC-08): cálculos y validaciones que dan resultados incorrectos o 500.
4. **Cierre de inconsistencias de proceso** (IC-01, IC-02, IC-10, IC-13): resolver PA-01/PA-07/PA-25 y sincronizar KB ↔ código ↔ CHANGES.md. Decidir si `Dictado` se implementa o se actualiza el ADR-006.
5. **Higiene** (R-08…R-18, Q-01…Q-05): logging, race conditions menores, tamaños de archivo, UI faltante (inbox/perfil), config Moodle por tenant.

> **Recomendación transversal**: generar el cliente HTTP del frontend desde el OpenAPI del backend y unificar prefijos bajo `/api/v1`. Eso elimina de raíz toda la familia R-04 y evita que vuelva a divergir.
