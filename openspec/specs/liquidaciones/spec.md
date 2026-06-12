# liquidaciones Specification

## Purpose
TBD - created by archiving change c-18-liquidaciones-y-honorarios. Update Purpose after archive.
## Requirements
### Requirement: Cálculo de liquidación del período por (cohorte × mes)

El sistema SHALL calcular la liquidación de honorarios del período `(cohorte_id, periodo)` (donde `periodo` es `AAAA-MM`) para cada `(usuario, rol)` con asignaciones activas en ese período. La unidad de operación es `(cohorte × mes)` (RN-37). Cohortes distintas tienen liquidaciones independientes.

#### Scenario: Calcular liquidación de un docente con base + plus
- **GIVEN** existe `SalarioBase(rol=PROFESOR, monto=100000, desde=2026-01-01, hasta=null)`, `SalarioPlus(grupo=PROG, rol=PROFESOR, monto=15000, tope=null)`, `MateriaGrupoPlus(materia=M1, grupo=PROG)`, y el docente U1 tiene asignación PROFESOR en una comisión de M1 vigente en `2026-03`
- **WHEN** un usuario FINANZAS hace `GET /api/liquidaciones/{cohorte_id}/2026-03`
- **THEN** la respuesta incluye una fila para `(U1, PROFESOR)` con `monto_base=100000`, `monto_plus=15000`, `total=115000`, `n_comisiones_detectadas=1`, `n_comisiones_acumuladas=1`.

#### Scenario: Acumulación sin tope
- **GIVEN** `SalarioPlus(grupo=PROG, rol=PROFESOR, monto=15000, tope=null)` y U1 tiene 4 comisiones de PROG en el período
- **WHEN** se calcula la liquidación
- **THEN** la fila tiene `monto_plus = 4 × 15000 = 60000` y `n_comisiones_acumuladas=4`.

#### Scenario: Acumulación con tope alcanza el límite
- **GIVEN** `SalarioPlus(grupo=BD, rol=TUTOR, monto=8000, tope=3)` y U2 tiene 5 comisiones de BD
- **WHEN** se calcula la liquidación
- **THEN** la fila tiene `monto_plus = 3 × 8000 = 24000`, `n_comisiones_detectadas=5`, `n_comisiones_acumuladas=3`, `tope_acumulacion=3`.

#### Scenario: Acumulación con tope no alcanzado
- **GIVEN** `SalarioPlus(grupo=BD, rol=TUTOR, monto=8000, tope=3)` y U2 tiene 2 comisiones de BD
- **WHEN** se calcula la liquidación
- **THEN** la fila tiene `monto_plus = 2 × 8000 = 16000`, `n_comisiones_detectadas=2`, `n_comisiones_acumuladas=2`.

#### Scenario: Docente con plus de múltiples grupos
- **GIVEN** U3 dicta 2 comisiones de PROG (plus=15000, sin tope) y 1 comisión de BD (plus=8000, sin tope) en el período
- **WHEN** se calcula la liquidación
- **THEN** la fila tiene `monto_plus = (2 × 15000) + (1 × 8000) = 38000` y el detalle desglosa los aportes por grupo.

#### Scenario: Materia sin grupo asignado no aporta plus
- **GIVEN** una materia M5 SIN fila vigente en `MateriaGrupoPlus`, y U4 dicta una comisión de M5
- **WHEN** se calcula la liquidación
- **THEN** U4 recibe solo `monto_base`, `monto_plus=0` por esa comisión.

#### Scenario: Docente sin SalarioBase vigente genera warning
- **GIVEN** no existe `SalarioBase` para `rol=NEXO` en el período y U5 tiene asignación NEXO
- **WHEN** se calcula la liquidación
- **THEN** la fila de U5 NO se genera y la respuesta incluye `warnings: [{ usuario_id: U5, rol: "NEXO", motivo: "SIN_BASE_VIGENTE" }]`, sin bloquear el cálculo del resto.

#### Scenario: Cálculo respeta vigencia retroactiva de la grilla
- **GIVEN** dos `SalarioBase` para PROFESOR: `(monto=100000, desde=2026-01-01, hasta=2026-05-31)` y `(monto=120000, desde=2026-06-01, hasta=null)`
- **WHEN** se calcula la liquidación de `periodo=2026-04`
- **THEN** la fila usa `monto_base=100000` (la vigente en abril), NO la vigente al momento del request.

---

### Requirement: Segmentación contable de la vista de liquidación

La respuesta del cálculo SHALL presentar tres segmentos diferenciados (F10.6, RN-36, RN-38):
1. **General**: filas con `rol ∈ {PROFESOR, TUTOR, COORDINADOR}` y `excluido_por_factura=false`.
2. **NEXO**: filas con `rol=NEXO` y `excluido_por_factura=false`. Aparecen separados pero SHALL sumar al `total_general`.
3. **Facturantes**: filas de usuarios con `Usuario.facturador=true` agrupadas informativamente. Estas filas SHALL marcarse con `excluido_por_factura=true` y NO sumar al `total_general`.

La respuesta SHALL incluir dos KPIs de cabecera: `total_sin_factura` (suma general + NEXO) y `total_con_factura` (suma facturantes).

#### Scenario: Vista con tres segmentos
- **GIVEN** el período tiene 3 docentes en relación de dependencia (1 PROFESOR, 1 TUTOR, 1 NEXO) y 2 docentes facturantes
- **WHEN** se hace `GET /api/liquidaciones/{cohorte_id}/{periodo}`
- **THEN** la respuesta tiene `segmentos.general: [PROFESOR, TUTOR]`, `segmentos.nexo: [NEXO]`, `segmentos.facturantes: [F1, F2]`, `total_sin_factura = total(general) + total(nexo)` y `total_con_factura = total(facturantes)`.

#### Scenario: Docente facturante no suma al total general
- **GIVEN** U6 tiene `facturador=true` y asignaciones activas con `total_calculado=150000` (informativo)
- **WHEN** se calcula la liquidación
- **THEN** la fila aparece en `segmentos.facturantes`, marcada con `excluido_por_factura=true`, y NO suma a `total_sin_factura`.

#### Scenario: NEXO separado pero sumando
- **GIVEN** U7 tiene rol NEXO con `total_calculado=80000`
- **WHEN** se calcula la liquidación
- **THEN** la fila aparece en `segmentos.nexo`, y `total_sin_factura` INCLUYE los 80000.

---

### Requirement: Cierre inmutable de liquidación

El sistema SHALL exponer `POST /api/liquidaciones/{cohorte_id}/{periodo}/cerrar` (permiso `liquidaciones:cerrar`, rol FINANZAS) que persiste los montos calculados en filas `Liquidacion` con `estado=Cerrada`. Una liquidación cerrada NO puede modificarse ni recalcularse. Toda mutación sobre filas con `estado=Cerrada` SHALL ser rechazada con `409 Conflict` desde el repository (no solo desde el router).

#### Scenario: Cierre exitoso
- **WHEN** un usuario FINANZAS hace `POST /api/liquidaciones/{cohorte_id}/2026-03/cerrar` con body `{ "confirmar_cierre": true, "periodo": "2026-03" }`
- **THEN** el sistema persiste las filas calculadas con `estado=Cerrada`, snapshot del flag `excluido_por_factura` por usuario, devuelve `200 OK` con el resumen, y registra `LIQUIDACION_CERRAR` en el audit log con `detalle: { cohorte_id, periodo, total_filas, total_sin_factura, total_con_factura }`.

#### Scenario: Cierre rechaza confirmación inválida
- **WHEN** un usuario FINANZAS hace `POST .../cerrar` con body `{ "confirmar_cierre": false, "periodo": "2026-03" }`
- **THEN** el sistema responde `400 Bad Request` con `{ "error": "confirmacion_requerida" }`.

#### Scenario: Cierre rechaza mismatch de periodo
- **WHEN** un usuario FINANZAS hace `POST /api/liquidaciones/{cohorte_id}/2026-03/cerrar` con body `{ "confirmar_cierre": true, "periodo": "2026-04" }`
- **THEN** el sistema responde `400 Bad Request` con `{ "error": "periodo_mismatch" }` (defensa contra TOCTOU).

#### Scenario: Doble cierre del mismo período
- **WHEN** ya existe liquidación cerrada para `(cohorte_id, 2026-03)` y un usuario FINANZAS hace `POST .../cerrar` de nuevo
- **THEN** el sistema responde `409 Conflict` con `{ "error": "periodo_ya_cerrado" }`.

#### Scenario: Modificación de liquidación cerrada rechazada en repository
- **GIVEN** una `Liquidacion` con `estado=Cerrada`
- **WHEN** cualquier llamada (vía router o vía service interno) intenta `UPDATE` o `DELETE` sobre esa fila
- **THEN** el repository lanza `LiquidacionCerradaError` que el router traduce a `409 Conflict` con `{ "error": "liquidacion_inmutable" }`.

#### Scenario: GET sobre liquidación cerrada devuelve snapshot
- **WHEN** se hace `GET /api/liquidaciones/{cohorte_id}/{periodo}` para un período ya cerrado
- **THEN** la respuesta devuelve los montos persistidos (no recalcula), con `estado: "Cerrada"`, `cerrada_at`, `cerrada_por_usuario_id`.

#### Scenario: GET sobre periodo no cerrado recalcula on-demand
- **WHEN** se hace `GET /api/liquidaciones/{cohorte_id}/{periodo}` para un período abierto
- **THEN** la respuesta recalcula los montos con la grilla actual y NO persiste cambios.

---

### Requirement: Permisos `liquidaciones:*` con fail-closed

Todos los endpoints `/api/liquidaciones/*` SHALL aplicar `require_permission` con los siguientes permisos:

- `liquidaciones:calcular` — disparar el cálculo de un período.
- `liquidaciones:ver` — ver liquidación (actual o histórica).
- `liquidaciones:exportar` — obtener la respuesta serializada para exportación externa.
- `liquidaciones:cerrar` — ejecutar el cierre inmutable.
- `liquidaciones:configurar-salarios` — modificar la grilla salarial (cubierto por capability `grilla-salarial`).

Por defecto, FINANZAS SHALL recibir TODOS estos permisos; ADMIN recibe solo `liquidaciones:ver`. Otros roles NO tienen acceso.

#### Scenario: Usuario sin permiso recibe 403
- **WHEN** un usuario COORDINADOR (sin `liquidaciones:ver`) hace `GET /api/liquidaciones/{cohorte_id}/{periodo}`
- **THEN** el sistema responde `403 Forbidden` y NO ejecuta el cálculo.

#### Scenario: Usuario ADMIN solo puede ver
- **WHEN** un usuario ADMIN hace `POST /api/liquidaciones/{cohorte_id}/{periodo}/cerrar`
- **THEN** el sistema responde `403 Forbidden`.

#### Scenario: Fail-closed sin asignación de permiso
- **GIVEN** un rol nuevo X creado sin `liquidaciones:*`
- **WHEN** un usuario con rol X hace cualquier llamada a `/api/liquidaciones/*`
- **THEN** el sistema responde `403 Forbidden` (no `404` ni `500`).

---

### Requirement: Identidad y tenant siempre desde JWT

Toda llamada a `/api/liquidaciones/*` y `/api/facturas/*` SHALL derivar `usuario_id`, `roles` y `tenant_id` exclusivamente del JWT verificado. El sistema MUST ignorar cualquier `tenant_id`, `actor_id` o equivalente presente en body, query o path.

#### Scenario: tenant_id en body es ignorado
- **WHEN** un usuario FINANZAS de `tenant_A` envía `POST /api/liquidaciones/.../cerrar` con body que incluye `{ "tenant_id": "tenant_B", ... }`
- **THEN** el sistema procesa la operación sobre `tenant_A` (del JWT), ignora el `tenant_id` del body, y el audit log registra `tenant_id=tenant_A`.

#### Scenario: Cross-tenant rechazado
- **WHEN** un usuario FINANZAS de `tenant_A` hace `GET /api/liquidaciones/{cohorte_id_de_tenant_B}/{periodo}`
- **THEN** el sistema responde `404 Not Found` (el repository filtra por tenant del JWT y no encuentra la cohorte).

---

### Requirement: Historial de liquidaciones cerradas

El sistema SHALL exponer `GET /api/liquidaciones/historial` (permiso `liquidaciones:ver`) que lista los períodos cerrados del tenant, opcionalmente filtrados por `cohorte_id`, rango de períodos o `usuario_id`. La respuesta es paginada y ordenada por `(periodo DESC, cohorte_id)`.

#### Scenario: Listado del historial
- **WHEN** un usuario FINANZAS hace `GET /api/liquidaciones/historial?cohorte_id=<uuid>&desde=2026-01&hasta=2026-06`
- **THEN** el sistema devuelve la lista paginada de períodos cerrados que matchean los filtros, con `total_filas`, `total_sin_factura`, `total_con_factura`, `cerrada_at`, `cerrada_por_usuario_id` por período.

#### Scenario: Filtrado por usuario
- **WHEN** un usuario FINANZAS hace `GET /api/liquidaciones/historial?usuario_id=<uuid>`
- **THEN** el sistema devuelve solo los períodos cerrados en los que ese usuario aparece, con su `total` por período.

---

### Requirement: Auditoría del cálculo y cierre

Todo cálculo de liquidación (GET sobre período abierto o cerrado) y todo cierre SHALL generar registros en el audit log con códigos `LIQUIDACION_CALCULAR` y `LIQUIDACION_CERRAR` respectivamente. El detalle JSON incluye `cohorte_id`, `periodo`, `total_filas`, `total_sin_factura`, `total_con_factura` y, en cierre, snapshot del calculador (versión de la grilla aplicada).

#### Scenario: GET genera evento de auditoría
- **WHEN** un usuario FINANZAS hace `GET /api/liquidaciones/{cohorte_id}/{periodo}`
- **THEN** se registra un audit log con `accion: "LIQUIDACION_CALCULAR"`, `detalle: { cohorte_id, periodo, modo: "abierta"|"cerrada", total_filas }`.

#### Scenario: Cierre genera evento de auditoría con totales
- **WHEN** un usuario FINANZAS cierra exitosamente un período
- **THEN** se registra un audit log con `accion: "LIQUIDACION_CERRAR"`, `detalle: { cohorte_id, periodo, total_filas, total_sin_factura, total_con_factura }`.

