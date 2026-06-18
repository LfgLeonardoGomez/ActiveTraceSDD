# Plan de Remediación — Secuencial vs Paralelo

> **Fecha**: 2026-06-17
> **Insumos**: [`docs/AUDITORIA-FALLAS.md`](AUDITORIA-FALLAS.md) + base de conocimiento (`knowledge-base/`, `docs/ARQUITECTURA.md`).
> **Objetivo**: clasificar cada hallazgo en *resolver individualmente* (secuencial / bloqueante) vs *paralelizable*, con la evidencia que lo justifica.

---

## Criterio de paralelización (la regla)

Dos arreglos pueden ejecutarse **en paralelo** sólo si se cumplen **ambas** condiciones:

1. **No comparten archivos** → no hay conflicto de merge.
2. **No hay dependencia lógica** → ninguno necesita que el otro exista primero.

Si comparten archivo **o** hay dependencia, van **secuenciales** (mismo dueño, mismo PR o en orden). La evidencia de cada decisión es el **conjunto de archivos que toca cada hallazgo** (tabla maestra abajo) y, donde aplica, la **dependencia de dominio según la KB**.

Gobernanza (CLAUDE.md): los dominios **CRÍTICOS** (auth, multi-tenancy, RBAC, audit log, liquidaciones, core-models) requieren **propuesta + aprobación humana** antes de escribir; no son autónomos aunque sean paralelizables.

---

## Tabla maestra — evidencia de archivos por hallazgo

| Hallazgo | Sev. | Dominio (governance) | Archivos que toca | Comparte archivo con |
|---|:--:|---|---|---|
| **R-01** Login roto | CRÍT | auth (**CRÍTICO**) | `routers/auth.py`, `tests/test_auth.py` | R-07, R-04(prefix), Q-02 |
| **R-07** Log impersonación ciphertext | ALTO | auth (**CRÍTICO**) | `routers/auth.py` | R-01, R-04, Q-02 |
| **R-02** Template comunicaciones | CRÍT | comunicaciones (MEDIO) | `services/comunicacion_service.py` | — |
| **R-08** N8N log spam | ALTO | comunicaciones (MEDIO) | `workers/comunicacion_worker.py` | R-14 |
| **R-14** resetear_colgados cada ciclo | MEDIO | comunicaciones (MEDIO) | `workers/comunicacion_worker.py` | R-08 |
| **R-17** get_pendientes no filtra aprobado | MEDIO | comunicaciones (MEDIO) | `repositories/comunicacion_repository.py` | — |
| **R-06** periodo sin validación | ALTO | liquidaciones (**CRÍTICO**) | `liquidaciones/.../liquidacion_calc_service.py`, `.../salario_base_repo.py` | R-18, IC-08 |
| **R-18** snapshot silencia JSON | MEDIO | liquidaciones (**CRÍTICO**) | `liquidaciones/.../liquidacion_calc_service.py` | R-06, IC-08 |
| **IC-08** RN-26 banco sin validar | MEDIO | liquidaciones (**CRÍTICO**) | `liquidaciones/.../liquidacion_calc_service.py` | R-06, R-18 |
| **R-13** Race cierre liquidación | MEDIO | liquidaciones (**CRÍTICO**) | `liquidaciones/.../liquidacion_cierre_service.py`, migración (constraint UNIQUE) | — (migración) |
| **IC-03** Permisos liquidaciones no se siembran | ALTO | RBAC+liq (**CRÍTICO**) | nueva migración / `liquidaciones/seed.py` / `main.py` lifespan | IC-07 (seeds RBAC) |
| **S-01** Hard delete EvaluacionCandidato | ALTO | audit/append-only (**CRÍTICO**) | `repositories/evaluacion_repository.py`, `models/evaluacion.py`, migración (deleted_at) | S-02, Q-02 |
| **S-02** text() sin tenant_id | MEDIO | tenancy (**CRÍTICO**) | `repositories/evaluacion_repository.py` | S-01, Q-02 |
| **IC-07** Permiso duplicado evaluacion:reservar | ALTO | RBAC (**CRÍTICO**) | migración seeds (`002`/`010`) | IC-03 (seeds RBAC) |
| **R-04** Prefijos API + frontend | CRÍT | api/ui (transversal) | backend routers `prefix=` (auth, analisis, comunicaciones, coloquios, avisos, tareas, programas, auditoria, fechas) + **todos** los `frontend/.../*.api.ts` | auth.py, varios |
| **R-11** Coordinación sin guard | ALTO | ui (BAJO) | `frontend/src/App.tsx` | R-12 |
| **R-12** Comisiones sin guard | ALTO | ui (BAJO) | `frontend/src/App.tsx` | R-11 |
| **R-09** Inbox sin UI | ALTO | ui (BAJO) | nuevo `frontend/features/inbox/*` | — |
| **R-10** Perfil sin UI | ALTO | ui (BAJO) | nuevo `frontend/features/perfil/*` | — |
| **R-03** Worker padrón no-op | CRÍT | moodle/tenancy (MEDIO) | `workers/main.py`, `models/tenant.py`, `workers/padron_sync_worker.py` | Q-01 (tenant.py) |
| **Q-01** Moodle/N8N global no por tenant | ALTO | integraciones (MEDIO) | `core/config.py`, `models/tenant.py`, `integrations/moodle_ws.py`, `n8n_client.py`, `routers/padron.py` | R-03 (tenant.py) |
| **Q-05** UI config Moodle | BAJO | ui (BAJO) | nuevo frontend + endpoint config tenant | depende Q-01/R-03 |
| **R-15** Settings() module-level | MEDIO | core (**CRÍTICO**) | `core/encryption.py`, `core/security.py`, `services/token_service.py` | — |
| **R-16** Descifrado silencia errores | MEDIO | seguridad (**CRÍTICO**) | `repositories/padron_repository.py`, `repositories/usuarios.py` | — |
| **IC-09** RN-28 CSRF no implementado | MEDIO | seguridad (**CRÍTICO**) | nuevo middleware (transversal) | — |
| **R-05** detectar_sin_corregir | ALTO | análisis (MEDIO) | `services/finalizacion_service.py` | — |
| **S-03** Hard delete RateLimitBucket | MEDIO | infra (BAJO) | `repositories/rate_limit_repository.py` | — |
| **IC-05** SlotEncuentro diverge E9 | ALTO | core-models (**CRÍTICO**) | `models/slot_encuentro.py`, migración | depende Gate 0 |
| **IC-06** Guardia diverge E11 | ALTO | core-models (**CRÍTICO**) | `models/guardia.py`, migración | depende Gate 0 |
| **IC-11** estado_academico:ver sin endpoint | MEDIO | alumnos (MEDIO) | nuevo router backend + frontend | depende R-04 |
| **Q-02** Archivos >500 LOC | MEDIO | refactor (BAJO) | split `analisis_repository.py`, `auth.py`, `evaluacion_repository.py` | R-01/R-07, S-01/S-02 |
| **Q-03** Componentes >200 LOC | MEDIO | refactor (BAJO) | 12 `.tsx` | posible con R-09…R-12 |
| **Q-04** as any / Zod | BAJO | refactor (BAJO) | `ConvocatoriaForm.tsx`, `AsignacionMasivaForm.tsx`, `ClonarEquipoForm.tsx` | — |
| **IC-04, IC-10, IC-12, IC-13, IC-14, IC-15** Sólo-doc | BAJO–MEDIO | docs | `knowledge-base/*.md`, `docs/ARQUITECTURA.md`, `CHANGES.md` | entre sí |

---

## GATE 0 — Decisiones bloqueantes (secuencial, PRIMERO)

Estas **no son fixes mecánicos**: son decisiones de arquitectura/producto (governance CRÍTICO) que **bloquean todo cambio de modelo de datos**. Hasta cerrarlas, **no tocar `models/` ni migraciones de estructura**.

| ID | Decisión | Bloquea a | Evidencia |
|---|---|---|---|
| **D1** | IC-01: ¿se implementa la entidad `Dictado` (ADR-006) o se actualiza el ADR para reflejar el modelo real `materia_id` directo? | IC-05, IC-06, Stream D (coloquios cuelgan de Dictado), encuentros/guardias | `docs/ARQUITECTURA.md:346` vs `models/` sin `Dictado` |
| **D2** | IC-02: cerrar formalmente PA-01 y PA-07 (ya asumidas en `Cohorte.carrera_id NOT NULL`) | cualquier cambio en `models/estructura.py` | `10_preguntas_abiertas.md:9,29` vs `estructura.py:76` |
| **D3** | IC-04: resolver la contradicción RN-05 (sin historial) vs E6 (versionado, ya implementado) | sincronización doc del padrón | `05_reglas_de_negocio.md:22` vs `04_modelo_de_datos.md:141` |

> **Por qué primero**: si D1 decide implementar `Dictado`, las FK de coloquios, encuentros y guardias cambian → arreglar IC-05/IC-06 o el modelo de evaluaciones **antes** de esa decisión sería trabajo tirado. Decidir D1/D2/D3 desbloquea o redirige todo lo de modelos.

---

## Streams paralelos (tras Gate 0)

Cada **stream** es independiente de los demás (no comparten archivos). **Dentro** de un stream, los ítems son secuenciales por compartir archivo/dominio.

### 🔴 Stream A — Auth (governance CRÍTICO → propuesta + aprobación)
**Secuencial interno** (todo en `routers/auth.py`): `R-01` → `R-07`.
Independiente del resto. **No paralelizable consigo mismo.**

### 🟡 Stream B — Comunicaciones (MEDIO)
3 sub-tracks, archivos distintos → **paralelizables entre sí**:
- `R-02` (`comunicacion_service.py`)
- `R-08` + `R-14` (mismo `comunicacion_worker.py` → juntos)
- `R-17` (`comunicacion_repository.py`)

### 🔴 Stream C — Liquidaciones (governance CRÍTICO → propuesta + aprobación)
- **Secuencial** (mismo `liquidacion_calc_service.py`): `R-06` → `R-18` → `IC-08`.
- **Paralelo a lo anterior**: `R-13` (cierre + migración constraint).

### 🔴 Stream D — Evaluaciones + RBAC seeds (governance CRÍTICO)
- **Secuencial** (mismo `evaluacion_repository.py`): `S-01` → `S-02`.
- `IC-07` + `IC-03` → **una sola migración de seeds RBAC** (ambos tocan seeds de permisos; coordinar para no duplicar).
- ⚠️ Si D1 = implementar `Dictado`, este stream espera a Gate 0 (las FK de coloquios cambian).

### 🟠 Stream E — Contrato API frontend↔backend (transversal, ALTA prioridad)
`R-04`: unificar prefijos backend a `/api/v1` + alinear **todos** los `*.api.ts`. **Bloquea la validación E2E** de casi toda la UI.
⚠️ Toca `auth.py` (línea `prefix=`) → **coordinar con Stream A** (mismo archivo): que el dueño de auth aplique R-01/R-07 y el cambio de prefijo en orden, no en paralelo ciego.

### 🟢 Stream F — Frontend guards + features faltantes (BAJO)
- `R-11` + `R-12` (mismo `App.tsx` → juntos).
- `R-09` (inbox) y `R-10` (perfil): archivos nuevos, **paralelos entre sí**. Dependencia **débil** de Stream E (sus endpoints ya están en `/api/v1`, pero conviene cerrar el contrato primero).

### 🟡 Stream G — Worker / Moodle / Tenant (MEDIO)
**Secuencial** (comparten `models/tenant.py`): `Q-01` (config por tenant) → `R-03` (worker consume esa config) → `Q-05` (UI de config, depende de ambos).

### 🔴 Stream H — Higiene de seguridad/core (governance CRÍTICO)
Archivos distintos → **paralelos entre sí**: `R-15` (lazy `Settings`), `R-16` (no silenciar descifrado), `IC-09` (middleware CSRF).

### 🟡 Stream J — Correctitud de análisis (MEDIO)
`R-05` (`finalizacion_service.py`) — aislado, paralelo a todo.

### 🟢 Stream I — Sincronización documental (BAJO, paralelo desde el minuto 0)
Sólo edita KB/docs, **no toca código** → corre en paralelo con TODO: `IC-10`, `IC-12`, `IC-13`, `IC-14`, `IC-15`, `S-03`(decisión doc), + actualizar la KB con el resultado de Gate 0.

---

## Matriz de conflictos — lo que NO se puede tocar a la vez

| Archivo / recurso | Hallazgos en conflicto | Resolución |
|---|---|---|
| `routers/auth.py` | R-01, R-07, R-04(prefix), Q-02(split) | Un solo dueño, en orden: R-01→R-07→prefix→split |
| `liquidacion_calc_service.py` | R-06, R-18, IC-08 | Secuencial, mismo PR |
| `evaluacion_repository.py` | S-01, S-02, Q-02(split) | Fixes (S-01→S-02) **antes** del split |
| `comunicacion_worker.py` | R-08, R-14 | Juntos |
| `frontend/src/App.tsx` | R-11, R-12 | Juntos |
| `models/tenant.py` | R-03, Q-01 | Secuencial (Q-01→R-03) |
| Seeds/migraciones RBAC | IC-03, IC-07 | Una migración conjunta |
| `models/` y migraciones de estructura | IC-01, IC-02, IC-05, IC-06 | **Bloqueados por Gate 0** |

---

## Orden de ejecución recomendado (olas)

```
OLA 0  (secuencial, gobernanza)      Gate 0: D1 → D2 → D3
                                     └─ en paralelo desde ya: Stream I (docs)

OLA 1  (paralela, multi-stream)      A │ B │ C │ D* │ E │ G │ H │ J
   * Stream D espera Gate 0 sólo si D1 = implementar Dictado
   ⚠ Coordinar A ↔ E (ambos tocan auth.py)

OLA 2  (depende de OLA 1)            F (R-09/R-10 tras E) │ Q-05 (tras G)
                                     IC-05 / IC-06 / IC-11 (tras Gate 0 + R-04)

OLA 3  (último, refactor)            K: Q-02 / Q-03 / Q-04
   Refactors DESPUÉS de los fixes funcionales en sus mismos archivos
   (Q-02 choca con A y D; Q-03 puede convivir con F).
```

### Resumen de paralelismo máximo en OLA 1
Hasta **8 streams concurrentes** (A, B, C, D, E, G, H, J) + docs (I). Cuello de botella de coordinación: `auth.py` (A↔E) y los seeds RBAC (IC-03↔IC-07).

---

## Qué se resuelve SÍ o SÍ individualmente (no paralelizable)

1. **Gate 0 (D1/D2/D3)** — decisiones, bloquean modelos. Primero y solo.
2. **Stream A (R-01→R-07)** — mismo archivo + dominio CRÍTICO con aprobación.
3. **Cadena de `liquidacion_calc_service.py` (R-06→R-18→IC-08)** — mismo archivo.
4. **Cadena de `evaluacion_repository.py` (S-01→S-02)** — mismo archivo.
5. **Cadena `tenant.py` (Q-01→R-03→Q-05)** — mismo archivo + dependencia lógica.
6. **Refactors Q-02** — después de los fixes que tocan esos mismos archivos.

## Qué es claramente paralelizable (sin choque)
- Streams **B, C, D, E, G, H, J** entre sí (dominios y archivos distintos).
- **Stream I (docs)** con absolutamente todo.
- Dentro de B: los 3 sub-tracks. Dentro de H: los 3 fixes. R-09 ∥ R-10.
