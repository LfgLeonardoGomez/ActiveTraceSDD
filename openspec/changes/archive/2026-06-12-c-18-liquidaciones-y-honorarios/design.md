## Context

Liquidaciones es el dominio contable núcleo del producto: convierte las asignaciones docentes del período en una grilla de honorarios `(Base + Plus = Total)` lista para pagar (o para excluir, en docentes facturantes). El módulo es **CRÍTICO** según el agent governance del proyecto: errores acá significan pagos incorrectos o ausentes y un cierre inmutable mal calculado contamina el histórico.

Estado actual del repo: ya existen los modelos base (`Tenant`, `Usuario` con `facturador: bool` y datos bancarios cifrados, `Carrera`, `Cohorte`, `Materia`, `Comision`, `Asignacion`), el módulo de RBAC (C-04) con `require_permission` y fail-closed, y el audit log (C-05) con catálogo cerrado de acciones. Este change agrega encima cinco entidades nuevas y un servicio de cálculo determinístico.

Dos preguntas abiertas críticas se cierran en este change y ya están reflejadas en los modelos:

- **PA-22** (mapeo materia → grupo de Plus): se introduce `MateriaGrupoPlus` con vigencia. La decisión arquitectónica es que este mapeo vive en el módulo de liquidaciones, no en `estructura-academica`, porque es un atributo contable de la materia (qué Plus le corresponde) y no un atributo académico.
- **PA-23** (acumulación y tope de Plus): se introduce `SalarioPlus.tope_acumulacion` (DECIMAL NULLABLE). El default semántico es acumular sin tope (NULL); cualquier configuración con tope se especifica por instancia `(grupo × rol)`.

Stakeholders: FINANZAS (operador principal), ADMIN (lectura del histórico y vista global), Coordinación (informativo: no opera el módulo).

Restricciones duras heredadas del proyecto:
- Identidad SIEMPRE desde JWT — nunca desde body / query / path.
- Multi-tenancy row-level — `tenant_id` en cada tabla y filtrado por defecto en los repositories.
- RBAC fail-closed con `require_permission`.
- Soft delete en todas las entidades (auditoría append-only).
- PII (CBU) cifrado AES-256 — ya garantizado por `Usuario` desde C-03.
- Strict TDD: test que falla → código mínimo → triangulación → refactor. Cobertura ≥80% líneas, ≥90% reglas de negocio.
- Una sola migración Alembic para todo el change.

## Goals / Non-Goals

**Goals:**
- Calcular determinísticamente `Total = Base(rol, periodo) + Σ Plus(grupo, rol, periodo) × N_comisiones_acumuladas` para cada `(usuario, rol, cohorte, periodo)`.
- Cerrar un `(cohorte, periodo)` de forma **inmutable**: rechazar toda mutación posterior con `409 Conflict`.
- Versionar las tres tablas de grilla salarial (`SalarioBase`, `SalarioPlus`, `MateriaGrupoPlus`) con `desde / hasta` y prohibir solapamientos de vigencia.
- Aplicar el **tope de acumulación** por instancia `(grupo, rol)`: `N_acumulado = min(N_comisiones_del_grupo, tope_acumulacion)` cuando `tope_acumulacion IS NOT NULL`.
- Excluir docentes facturantes (`Usuario.facturador = true`) de la liquidación general y gestionar su pago vía `Factura` (Pendiente → Abonada).
- Presentar tres segmentos contables: general, NEXO (separado pero suma al total), facturantes (informativo, excluido del total).
- Auditar todos los eventos significativos (cálculo, cierre, modificación de grilla, ABM de facturas) con el catálogo cerrado de acciones.

**Non-Goals:**
- **NO** se implementa el frontend de F10.1–F10.6 acá. Se exponen solo los endpoints REST; el frontend se aborda en C-22 o un change posterior.
- **NO** se generan PDFs ni planillas Excel de exportación: el endpoint `liquidaciones:exportar` retorna JSON serializable (la conversión a archivo es responsabilidad del consumidor o de un change futuro).
- **NO** hay integración con sistemas de pago externos (ni transferencia bancaria, ni AFIP, ni emisión de facturas hacia el docente).
- **NO** se modela retroactividad: si `SalarioBase` se modifica con fecha pasada, las liquidaciones ya `Cerradas` permanecen inmutables (RN-22). El nuevo monto solo aplica a liquidaciones `Abiertas` y períodos futuros.
- **NO** se modela "ajuste manual" sobre una liquidación cerrada — si hay error, se requiere reabrir un período por una vía administrativa fuera del scope (queda como pregunta abierta para change futuro, si se necesita).
- **NO** se modela la modalidad "mixta" de cobro (un docente factura algunas materias y otras no). PA-23 + RN-35 asumen que `Usuario.facturador` es binario y aplica a TODA la liquidación del usuario.

## Decisions

### D1 — `MateriaGrupoPlus` vive en el módulo de liquidaciones (no en estructura-academica)

**Decisión**: cerrar PA-22 alojando `MateriaGrupoPlus(id, tenant_id, materia_id, grupo, desde, hasta)` en `app/modules/liquidaciones/models/materia_grupo_plus.py`.

**Por qué**: el grupo de Plus es un atributo **contable** de la materia (qué Plus paga al docente), no un atributo académico (qué se enseña). Acoplarlo a `Materia` (módulo de estructura-academica, C-06) generaría una dependencia inversa: estructura-academica no debe saber de liquidaciones. El módulo de liquidaciones, en cambio, ya depende de `materia_id` (FK), por lo cual el mapeo vive donde se consume.

**Alternativas consideradas**:
- *Columna `grupo_plus` en `Materia`*: simple, pero rompe el historial. Si una materia se recategoriza de "PROG" a "PROG_AVANZADA", las liquidaciones cerradas que la calcularon como "PROG" deberían poder reproducir su cálculo — y con una columna mutable se pierde esa capacidad. Descartado.
- *Tabla puente en `estructura-academica`*: mantiene el historial, pero acopla un módulo bajo (CRUDs catálogos) a un dominio CRÍTICO (liquidaciones). Descartado por governance.

**Implicancia**: las consultas de cálculo (`liquidaciones_service.calcular_periodo`) hacen JOIN entre `Asignacion → Materia → MateriaGrupoPlus` filtrando por `desde <= periodo <= COALESCE(hasta, '9999-12-31')`.

### D2 — `SalarioPlus.tope_acumulacion DECIMAL NULLABLE` (no INTEGER)

**Decisión**: cerrar PA-23 con `tope_acumulacion: DECIMAL NULLABLE` donde NULL = sin tope.

**Por qué**: aunque conceptualmente el tope es entero (cantidad de comisiones), usar `DECIMAL` permite codificar futuros casos de "tope fraccional" (ej: 1.5 implicaría "una comisión completa + una a la mitad") sin migración. Costo prácticamente nulo, flexibilidad futura. Validamos en el service que el valor sea positivo y, por convención, entero en este release.

**Algoritmo de acumulación** (RN-33 + PA-23):
```
para cada (grupo, rol) aplicable al usuario en el periodo:
    N_comisiones = count(asignaciones del usuario en materias mapeadas a `grupo` y vigentes en el periodo)
    tope = SalarioPlus.tope_acumulacion vigente en el periodo (puede ser NULL)
    N_efectivo = min(N_comisiones, tope) si tope IS NOT NULL else N_comisiones
    monto_plus_acumulado += SalarioPlus.monto × N_efectivo
```

**Alternativas consideradas**:
- *Tope global por rol en `SalarioBase`*: insuficiente — el tope debe variar por grupo.
- *No tope (RN-33 estricto, infinito)*: simple, pero el usuario pidió explícitamente la opción en PA-23. Descartado.

### D3 — Cierre inmutable: estado `Cerrada` + guard en el repository

**Decisión**: `Liquidacion.estado ∈ {Abierta, Cerrada}`. Toda mutación (PATCH, DELETE, recálculo) sobre filas en estado `Cerrada` retorna `409 Conflict` desde el repository (no desde el router), de modo que ningún punto de entrada pueda saltarse el guard.

**Por qué**: la inmutabilidad es contractual (RN-22). Si el guard vive en el router, una llamada interna desde otro service (recálculo masivo, migración de datos) podría bypassearlo. Poniéndolo en el repository garantizamos que la única forma de mutar una fila cerrada es reabrir explícitamente vía un método dedicado, que en este change NO se implementa.

**Estados y transiciones**:
- `Abierta → Cerrada`: vía endpoint `POST /api/liquidaciones/{cohorte_id}/{periodo}/cerrar`, requiere `liquidaciones:cerrar`. Emite `LIQUIDACION_CERRAR` en audit log.
- `Cerrada → Abierta`: **NO se permite en este change**. Si el negocio lo necesita, será un change futuro con doble aprobación.

### D4 — Cálculo determinístico y sin caché — recálculo on-demand mientras `Abierta`

**Decisión**: mientras una liquidación está `Abierta`, cada vista (`GET /api/liquidaciones/{cohorte_id}/{periodo}`) **recalcula** los montos al vuelo a partir de la grilla vigente y las asignaciones del período. Los montos persistidos en `Liquidacion` solo se "congelan" en el momento del cierre.

**Por qué**: garantiza que el operador FINANZAS siempre ve el cálculo más actual antes de cerrar. Evita el problema clásico de "liquidación calculada el día X, monto cambió el día X+1, operador cierra sin saber". El costo es bajo: el cálculo es O(N_docentes × N_grupos) por período, ejecutable en <500ms para tenants típicos.

**Trade-off**: una llamada GET no es idempotente en términos de "valor devuelto" si la grilla cambia entre llamadas — pero **sí** es idempotente en términos de side-effects (no escribe). El frontend debe mostrar la fecha/hora de cálculo. Al cerrar, los montos se persisten y la próxima GET sobre `Cerrada` devuelve los valores congelados.

### D5 — Restricción de no-solapamiento de vigencias en grilla

**Decisión**: en `SalarioBase`, `SalarioPlus` y `MateriaGrupoPlus`, agregar un check de integridad a nivel de servicio (no a nivel de DB exclusion constraint) que valide que no haya dos filas activas con `(tenant_id, rol)` (o `(tenant_id, grupo, rol)` o `(tenant_id, materia_id)`) y rangos `[desde, hasta]` superpuestos.

**Por qué**: la regla "solo una entrada vigente por clave en un instante dado" (RN-31) es de integridad de dominio. Las exclusion constraints de PostgreSQL (`EXCLUDE USING gist`) requieren la extensión `btree_gist` y complican la migración. Validar en el service mantiene la portabilidad y el control fino (mensajes de error claros). El costo es que un agente externo escribiendo directo en la DB podría romper la invariante — pero ese vector ya está prohibido por el proyecto (todo cambio vía el ORM).

**Algoritmo**: al INSERT / UPDATE en cualquiera de las tres tablas, el repository ejecuta:
```sql
SELECT 1 FROM <tabla>
WHERE tenant_id = :tenant_id
  AND <clave> = :clave
  AND id != :id
  AND deleted_at IS NULL
  AND tstzrange(desde, COALESCE(hasta, 'infinity'), '[]')
    && tstzrange(:desde, COALESCE(:hasta, 'infinity'), '[]')
```
Si retorna filas → `409 Conflict` con mensaje `"Vigencia se solapa con registro existente <id>"`.

### D6 — Facturas: archivo persistido vía `referencia_archivo`, no en DB

**Decisión**: `Factura.referencia_archivo: str` apunta a un identificador opaco del servicio de almacenamiento (S3 / equivalente). El archivo NO se guarda en PostgreSQL.

**Por qué**: convención del proyecto (E20 ya define `referencia_archivo`). Mantener PostgreSQL liviano y permitir backup/replicación independiente del storage.

**Implicancia**: este change NO implementa el storage; expone una interfaz `FileStoragePort` con un stub que registra el archivo en memoria/disco local de dev. El binding a S3 será un change de infra posterior (probablemente parte de C-23 / C-24).

### D7 — Una migración Alembic única

**Decisión**: una sola revisión Alembic `<rev>_c18_liquidaciones.py` que crea las cinco tablas, sus índices y FKs.

**Por qué**: regla dura del proyecto. Facilita rollback (down() destruye todo el dominio en una sola operación).

**Índices propuestos**:
- `salario_base`: `(tenant_id, rol, desde DESC)`.
- `salario_plus`: `(tenant_id, grupo, rol, desde DESC)`.
- `materia_grupo_plus`: `(tenant_id, materia_id, desde DESC)` y `(tenant_id, grupo)` para reverse lookup.
- `liquidacion`: `(tenant_id, cohorte_id, periodo)` único parcial donde `deleted_at IS NULL` para una fila por `(usuario, rol)` dentro del período. Y `(tenant_id, estado)` para queries por estado.
- `factura`: `(tenant_id, usuario_id, periodo)` y `(tenant_id, estado)`.

### D8 — Permisos sembrados pero no migrados desde C-04

**Decisión**: este change agrega al catálogo de permisos los códigos `liquidaciones:*` y `facturas:*` vía una función seed `seed_liquidaciones_permissions()` invocada en startup o en la migración (data migration), no en una migración separada del módulo C-04.

**Por qué**: C-04 expone una API de seed para que cada módulo registre sus permisos sin tocar al módulo de RBAC. Mantiene el desacople. Asignación por defecto: rol FINANZAS recibe todos los `liquidaciones:*` y `facturas:*`; ADMIN recibe solo los `*:ver`.

## Risks / Trade-offs

- **[Riesgo]** Cálculo de liquidación con grilla salarial inconsistente (ej: dos `SalarioBase` con vigencia solapada por bug en validación) → **Mitigación**: D5 valida en el service + tests específicos de overlap + alerta en el cálculo si el repository devuelve más de un registro para una `(rol, periodo)` (loguea y rechaza el cálculo del período).
- **[Riesgo]** Performance del cálculo on-demand (D4) en tenants grandes (1000+ docentes) → **Mitigación**: el algoritmo es lineal sobre asignaciones del período. Tests de carga con 1000 docentes × 20 grupos en CI. Si supera 1s, evaluamos caché por `(cohorte, periodo, grilla_version_hash)` en un change posterior.
- **[Riesgo]** Tope de acumulación mal documentado → docente cobra menos de lo esperado → **Mitigación**: el GET de liquidación retorna, por cada plus aplicado, los campos `n_comisiones_detectadas`, `n_comisiones_acumuladas`, `tope_acumulacion` para que la UI muestre explícitamente el cap.
- **[Riesgo]** Cierre accidental de un período (mass-cierre vía un cliente automatizado) → **Mitigación**: el endpoint de cierre requiere `liquidaciones:cerrar` (solo FINANZAS) + body con confirmación explícita (`{ "confirmar_cierre": true, "periodo": "AAAA-MM" }`). El campo `periodo` del body debe coincidir con el de la URL — defensa contra TOCTOU.
- **[Riesgo]** Docente cambia de modalidad `facturador` mid-período → **Mitigación**: snapshot del flag `Usuario.facturador` se persiste en `Liquidacion.excluido_por_factura` al momento del cierre. Mientras esté `Abierta`, refleja el estado actual del usuario.
- **[Trade-off]** No usar exclusion constraints de PostgreSQL (D5) → la integridad depende del service. **Aceptado**: portabilidad y control de errores son prioritarios; el bypass directo a DB está prohibido por convención.
- **[Trade-off]** No persistir el cálculo mientras está `Abierta` (D4) → recompute en cada GET. **Aceptado**: simplicidad y consistencia con la grilla actual son prioritarias frente al ahorro de CPU.

## Migration Plan

1. **Schema migration** (única revisión Alembic):
   - Crear tablas `salario_base`, `salario_plus`, `materia_grupo_plus`, `liquidacion`, `factura`.
   - Crear índices descritos en D7.
   - Habilitar extensión `btree_gist` **NO** (decisión D5).
2. **Seed de permisos**: invocar `seed_liquidaciones_permissions()` que llama al API de C-04 con la lista de `liquidaciones:*` y `facturas:*` y los asigna a FINANZAS / ADMIN según D8.
3. **Seed de audit codes**: registrar `LIQUIDACION_CERRAR`, `LIQUIDACION_CALCULAR`, `SALARIO_BASE_MODIFICAR`, `SALARIO_PLUS_MODIFICAR`, `MATERIA_GRUPO_PLUS_MODIFICAR`, `FACTURA_CARGAR`, `FACTURA_ABONAR` en el catálogo cerrado (RN-24, via API de C-05).
4. **Rollback**: la migración down() elimina las cinco tablas + revoca los permisos + des-registra los audit codes. Si hay liquidaciones cerradas históricas, el rollback DEBE fallar — el down() valida `count(liquidacion WHERE estado = 'Cerrada') == 0` antes de proceder. Si hay datos, requiere acción manual (export + truncate explícito por DBA).

**Despliegue**: feature-flag opcional `LIQUIDACIONES_ENABLED` por tenant — permite gradual rollout. Default: `true` en dev/staging; configurable por tenant en prod.

## Open Questions

- **OQ-1**: ¿Necesita el módulo soportar "reabrir" un período cerrado por excepción contable? El usuario no lo pidió, pero contablemente puede aparecer. **Propuesta**: difer a change futuro con doble aprobación humana + audit `LIQUIDACION_REABRIR`. No lo cubrimos acá.
- **OQ-2**: ¿Cómo se calcula la liquidación de un docente con asignaciones en **varias cohortes** dentro del mismo período? La unidad es `(cohorte × mes)` (RN-37), por lo tanto se generan filas independientes por cohorte. **Confirmado** — pero requiere validar con FINANZAS que esto matchea la práctica contable (si el docente recibe un único pago consolidado o uno por cohorte). Asumimos consolidado por **docente** al exportar (suma de todas las cohortes); las filas internas siguen siendo por cohorte.
- **OQ-3**: ¿Qué hacer si un docente NO tiene `SalarioBase` para su rol en el período (gap en la grilla)? **Propuesta**: el cálculo NO genera fila para ese docente y retorna un warning estructurado en la respuesta del GET (`warnings: [{ usuario_id, rol, motivo: "SIN_BASE_VIGENTE" }]`). El operador FINANZAS resuelve antes de cerrar. No bloquea el cierre del resto.
- **OQ-4**: ¿Las facturas pueden ser canceladas (de `Pendiente` a un estado `Cancelada`)? RN-39 dice que hay **exactamente dos** estados. **Confirmado**: solo Pendiente / Abonada. Si una factura es errónea, se hace soft delete (no transición a otro estado).
