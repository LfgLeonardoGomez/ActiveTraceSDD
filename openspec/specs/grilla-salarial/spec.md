# grilla-salarial Specification

## Purpose
TBD - created by archiving change c-18-liquidaciones-y-honorarios. Update Purpose after archive.
## Requirements
### Requirement: ABM de Salario Base por rol con vigencia temporal

El sistema SHALL permitir al rol FINANZAS (con permiso `liquidaciones:configurar-salarios`) crear, modificar, soft-eliminar y listar entradas de `SalarioBase`, donde cada entrada define el monto base de un rol docente con un rango de vigencia `[desde, hasta]`. El campo `hasta` MUST poder ser nulo (vigencia abierta). El par `(tenant_id, rol, [desde, hasta])` MUST NOT solaparse con otra entrada activa del mismo `(tenant_id, rol)`.

#### Scenario: Crear SalarioBase con vigencia abierta
- **WHEN** un usuario FINANZAS hace `POST /api/liquidaciones/salario-base` con `{ rol: "PROFESOR", monto: 100000, desde: "2026-01-01", hasta: null }`
- **THEN** el sistema crea la fila, devuelve `201 Created` con el `id`, y registra el evento `SALARIO_BASE_MODIFICAR` en el audit log con `accion: "CREATE"`.

#### Scenario: Rechazar solapamiento de vigencia
- **WHEN** existe `SalarioBase(rol=PROFESOR, desde=2026-01-01, hasta=null)` y un usuario FINANZAS hace `POST` con `{ rol: "PROFESOR", monto: 120000, desde: "2026-06-01", hasta: null }`
- **THEN** el sistema responde `409 Conflict` con `{ "error": "vigencia_solapada", "detalle": "Vigencia se solapa con registro existente <id>" }` y NO crea la nueva fila.

#### Scenario: Cerrar vigencia anterior y crear nueva
- **WHEN** un usuario FINANZAS hace `PATCH /api/liquidaciones/salario-base/{id}` con `{ hasta: "2026-05-31" }` y luego `POST` con `{ rol: "PROFESOR", monto: 120000, desde: "2026-06-01", hasta: null }`
- **THEN** el sistema acepta ambas operaciones, el rango original queda cerrado en `2026-05-31` y la nueva entrada inicia en `2026-06-01`, sin solapamiento.

#### Scenario: Soft delete preserva el histórico
- **WHEN** un usuario FINANZAS hace `DELETE /api/liquidaciones/salario-base/{id}`
- **THEN** el sistema marca `deleted_at`, la fila NO aparece en listados activos, pero permanece consultable para liquidaciones cerradas que la referenciaron.

#### Scenario: Acceso sin permiso es rechazado
- **WHEN** un usuario con rol COORDINADOR (sin `liquidaciones:configurar-salarios`) hace `POST /api/liquidaciones/salario-base`
- **THEN** el sistema responde `403 Forbidden` y NO modifica datos.

#### Scenario: Identidad y tenant desde JWT
- **WHEN** un usuario FINANZAS de `tenant_A` hace cualquier operación sobre `SalarioBase`
- **THEN** el sistema toma `tenant_id` y `usuario_id` exclusivamente del JWT verificado, ignora cualquier `tenant_id` en body / URL, y el repository filtra automáticamente por `tenant_A`.

---

### Requirement: ABM de Salario Plus por (grupo × rol) con tope de acumulación opcional

El sistema SHALL permitir al rol FINANZAS (con permiso `liquidaciones:configurar-salarios`) crear, modificar, soft-eliminar y listar entradas de `SalarioPlus`, donde cada entrada define el monto plus para una combinación `(grupo, rol)` con vigencia `[desde, hasta]` y un campo opcional `tope_acumulacion DECIMAL NULLABLE`. Cuando `tope_acumulacion` es NULL, no hay tope de acumulación. Cuando es un número positivo, ese es el máximo de comisiones del grupo que acumulan plus para el docente.

#### Scenario: Crear SalarioPlus sin tope
- **WHEN** un usuario FINANZAS hace `POST /api/liquidaciones/salario-plus` con `{ grupo: "PROG", rol: "PROFESOR", descripcion: "Plus Programación", monto: 15000, desde: "2026-01-01", hasta: null, tope_acumulacion: null }`
- **THEN** el sistema crea la fila, devuelve `201 Created` y registra `SALARIO_PLUS_MODIFICAR` en el audit log.

#### Scenario: Crear SalarioPlus con tope
- **WHEN** un usuario FINANZAS hace `POST` con `{ grupo: "BD", rol: "TUTOR", descripcion: "Plus Bases de Datos", monto: 8000, desde: "2026-01-01", hasta: null, tope_acumulacion: 3 }`
- **THEN** el sistema crea la fila y futuras liquidaciones aplican máximo `3 × 8000` aunque el docente dicte más de 3 comisiones del grupo BD.

#### Scenario: Rechazar tope negativo o cero
- **WHEN** un usuario FINANZAS hace `POST` con `tope_acumulacion: 0` o `tope_acumulacion: -1`
- **THEN** el sistema responde `422 Unprocessable Entity` con `{ "error": "tope_acumulacion_invalido" }` (Pydantic v2 con `extra='forbid'` y validador custom).

#### Scenario: Rechazar solapamiento de vigencia por (grupo × rol)
- **WHEN** existe `SalarioPlus(grupo=PROG, rol=PROFESOR, desde=2026-01-01, hasta=null)` y se intenta crear otra con `(grupo=PROG, rol=PROFESOR, desde=2026-06-01, hasta=null)`
- **THEN** el sistema responde `409 Conflict` y NO crea la nueva fila.

#### Scenario: Solapamiento NO se aplica entre grupos distintos
- **WHEN** existe `SalarioPlus(grupo=PROG, rol=PROFESOR, desde=2026-01-01, hasta=null)` y se crea `(grupo=BD, rol=PROFESOR, desde=2026-01-01, hasta=null)`
- **THEN** el sistema acepta ambas filas (distinto grupo).

---

### Requirement: ABM del mapeo Materia → Grupo de Plus con vigencia

El sistema SHALL exponer una entidad `MateriaGrupoPlus(id, tenant_id, materia_id, grupo, desde, hasta)` que mapea cada materia del tenant a una clave de grupo (ej: "PROG", "BD", "MAT") con vigencia temporal. Esta tabla vive en el módulo de liquidaciones (no en estructura-academica) y se mantiene versionada para preservar el cálculo histórico ante recategorización de materias.

#### Scenario: Asignar grupo a una materia
- **WHEN** un usuario FINANZAS hace `POST /api/liquidaciones/materia-grupo-plus` con `{ materia_id: "<uuid>", grupo: "PROG", desde: "2026-01-01", hasta: null }`
- **THEN** el sistema crea la fila, devuelve `201 Created` y registra `MATERIA_GRUPO_PLUS_MODIFICAR` en el audit log.

#### Scenario: Recategorizar materia preserva historial
- **WHEN** existe `MateriaGrupoPlus(materia_id=M1, grupo=PROG, desde=2026-01-01, hasta=null)` y un usuario FINANZAS hace `PATCH` cerrando `hasta=2026-05-31` y luego `POST` con `(M1, "PROG_AVANZADA", 2026-06-01, null)`
- **THEN** ambas filas coexisten, las liquidaciones de `2026-03` siguen calculando con grupo PROG y las de `2026-07` calculan con PROG_AVANZADA.

#### Scenario: Rechazar solapamiento de vigencia para la misma materia
- **WHEN** existe `MateriaGrupoPlus(materia_id=M1, grupo=PROG, desde=2026-01-01, hasta=null)` y se intenta crear `(M1, "BD", 2026-06-01, null)` sin cerrar la anterior
- **THEN** el sistema responde `409 Conflict` y NO crea la nueva fila.

#### Scenario: Una materia puede mapear a grupo nulo
- **WHEN** una materia del tenant NO tiene ninguna fila vigente en `MateriaGrupoPlus`
- **THEN** las asignaciones a esa materia NO generan ningún plus en la liquidación (solo aporta a la base).

#### Scenario: Multi-tenancy aplicada
- **WHEN** un usuario FINANZAS de `tenant_A` hace `GET /api/liquidaciones/materia-grupo-plus`
- **THEN** el sistema devuelve únicamente filas de `tenant_A`, incluso si un `materia_id` de otro tenant fuera enviado en el filtro.

---

### Requirement: Vigencia temporal sin solapamientos en las tres tablas de grilla

Las tablas `SalarioBase`, `SalarioPlus` y `MateriaGrupoPlus` SHALL mantener la invariante de no-solapamiento de vigencia por clave de negocio (`rol`, `(grupo, rol)`, `materia_id` respectivamente). La validación se ejecuta en el repository en cada INSERT o UPDATE.

#### Scenario: Resolver registro vigente en un período
- **WHEN** el servicio de cálculo busca `SalarioBase` para `rol=PROFESOR` y `periodo=2026-03`
- **THEN** el repository devuelve la única fila con `desde <= 2026-03-31 AND (hasta IS NULL OR hasta >= 2026-03-01)` y `deleted_at IS NULL`.

#### Scenario: No hay vigente devuelve None
- **WHEN** no existe `SalarioBase` para `rol=NEXO` en `periodo=2026-03`
- **THEN** el repository devuelve `None` y el servicio de cálculo agrega un warning estructurado `{ rol: "NEXO", motivo: "SIN_BASE_VIGENTE" }` a la respuesta del GET, SIN bloquear el cálculo del resto de docentes.

---

### Requirement: Auditoría obligatoria de modificaciones de grilla salarial

Toda creación, modificación o eliminación de filas en `SalarioBase`, `SalarioPlus` o `MateriaGrupoPlus` SHALL generar un registro en el audit log (E-AUD) con el código de acción correspondiente, el `actor_id` derivado del JWT, el detalle JSON con el diff (campos antes / después) y el `tenant_id` activo.

#### Scenario: Audit log registra creación
- **WHEN** un usuario FINANZAS crea exitosamente un `SalarioBase`
- **THEN** se inserta una fila en `audit_log` con `accion: "SALARIO_BASE_MODIFICAR"`, `detalle: { "operacion": "CREATE", "after": {...} }`, `actor_id` desde JWT y `filas_afectadas: 1`.

#### Scenario: Audit log registra modificación con diff
- **WHEN** un usuario FINANZAS hace `PATCH` cambiando `monto` de 100000 a 120000
- **THEN** se inserta una fila en `audit_log` con `detalle: { "operacion": "UPDATE", "before": { "monto": 100000 }, "after": { "monto": 120000 } }`.

#### Scenario: Audit log registra soft delete
- **WHEN** un usuario FINANZAS hace `DELETE` sobre una fila de grilla
- **THEN** se inserta una fila en `audit_log` con `detalle: { "operacion": "SOFT_DELETE" }` y la fila queda con `deleted_at` poblado pero permanece en la tabla.

---

### Requirement: UI — ABM SalarioBase (Frontend)

La UI SHALL permitir crear, editar y eliminar SalarioBase con rol, monto y vigencia.

#### Scenario: Crear SalarioBase
- **GIVEN** un usuario FINANZAS
- **WHEN** agrega un SalarioBase
- **THEN** la entrada aparece en la tabla

#### Scenario: Editar SalarioBase
- **GIVEN** una entrada existente
- **WHEN** se edita
- **THEN** la lista se actualiza

---

### Requirement: UI — ABM SalarioPlus (Frontend)

La UI SHALL permitir crear, editar y eliminar SalarioPlus con grupo, rol, monto y vigencia.

#### Scenario: Crear SalarioPlus
- **GIVEN** un usuario
- **WHEN** agrega un SalarioPlus
- **THEN** aparece en la tabla de Plus

---

### Requirement: UI — Alerta de conflicto de vigencia (Frontend)

La UI DEBE mostrar alertas inline de solapamiento de fechas.

#### Scenario: Solapamiento detectado
- **GIVEN** entradas solapadas para el mismo rol
- **WHEN** el usuario guarda
- **THEN** un mensaje inline aparece

---

### Requirement: UI — Filtros de grilla (Frontend)

La UI SHALL filtrar por rol y estado de vigencia.

#### Scenario: Filtro por rol
- **GIVEN** múltiples entradas
- **WHEN** se filtra por rol
- **THEN** solo las entradas que coinciden se muestran

