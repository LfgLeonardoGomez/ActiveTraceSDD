## ADDED Requirements

### Requirement: ABM de facturas de docentes facturantes

El sistema SHALL exponer endpoints `/api/facturas/*` (permisos `facturas:cargar`, `facturas:ver`, `facturas:abonar`, rol FINANZAS) para la gestión de comprobantes presentados por docentes con `Usuario.facturador=true`. Cada factura contiene: referencia al docente, `periodo (AAAA-MM)`, texto de detalle libre, `referencia_archivo` (puntero al archivo en el storage opaco), `tamano_kb`, fecha de carga, estado y fecha de pago.

#### Scenario: Cargar nueva factura
- **WHEN** un usuario FINANZAS hace `POST /api/facturas` con `{ usuario_id: U6, periodo: "2026-03", detalle: "Servicios docentes marzo", referencia_archivo: "<opaco>", tamano_kb: 245.3 }`
- **THEN** el sistema crea la fila con `estado=Pendiente`, `cargada_at=now`, devuelve `201 Created` con el `id`, y registra `FACTURA_CARGAR` en el audit log.

#### Scenario: Cargar factura para usuario no facturante es rechazado
- **WHEN** un usuario FINANZAS hace `POST /api/facturas` con `usuario_id` de un docente con `facturador=false`
- **THEN** el sistema responde `422 Unprocessable Entity` con `{ "error": "usuario_no_es_facturante" }` y NO crea la factura.

#### Scenario: Listar facturas con filtros
- **WHEN** un usuario FINANZAS hace `GET /api/facturas?usuario_id=<uuid>&estado=Pendiente&desde=2026-01&hasta=2026-06`
- **THEN** el sistema devuelve la lista paginada de facturas que matchean, ordenadas por `cargada_at DESC`.

#### Scenario: Búsqueda libre por detalle
- **WHEN** un usuario FINANZAS hace `GET /api/facturas?q=consultoria`
- **THEN** el sistema devuelve facturas cuyo campo `detalle` contiene la subcadena (case-insensitive).

---

### Requirement: Transición Pendiente → Abonada

El sistema SHALL exponer `POST /api/facturas/{id}/abonar` (permiso `facturas:abonar`) que cambia `estado` de `Pendiente` a `Abonada` y persiste `abonada_at=now`. Las facturas SHALL tener exactamente dos estados: `Pendiente` y `Abonada` (RN-39).

#### Scenario: Abonar factura pendiente
- **WHEN** una factura está en `estado=Pendiente` y un usuario FINANZAS hace `POST /api/facturas/{id}/abonar`
- **THEN** el sistema actualiza `estado=Abonada`, `abonada_at=now`, devuelve `200 OK` y registra `FACTURA_ABONAR` en el audit log con `detalle: { factura_id, usuario_id, periodo, monto: null }` (el monto no se modela; está en el archivo).

#### Scenario: Re-abonar factura ya abonada
- **WHEN** una factura está en `estado=Abonada` y se intenta `POST .../abonar` de nuevo
- **THEN** el sistema responde `409 Conflict` con `{ "error": "factura_ya_abonada" }`.

#### Scenario: No hay estado Cancelada
- **WHEN** se intenta cualquier transición a `Cancelada` (vía PATCH directo de `estado`)
- **THEN** el sistema responde `422 Unprocessable Entity` (Pydantic con `Enum` cerrado) y NO modifica la fila.

#### Scenario: Soft delete reemplaza cancelación
- **WHEN** una factura cargada por error se hace `DELETE /api/facturas/{id}`
- **THEN** el sistema marca `deleted_at`, la fila desaparece de listados activos pero permanece auditada.

---

### Requirement: Adjunto de factura vía referencia opaca

El archivo de la factura SHALL persistirse fuera de PostgreSQL, referenciado por `referencia_archivo: str` (puntero opaco al servicio de almacenamiento). El sistema SHALL exponer una interfaz `FileStoragePort` con métodos `upload(file) -> referencia` y `download(referencia) -> file`. El binding concreto (S3, disco local, etc.) es configuración de infraestructura.

#### Scenario: Upload de archivo y registro de factura
- **WHEN** un cliente sube un archivo PDF + metadatos vía `POST /api/facturas` (multipart o JSON con `referencia_archivo` precargado)
- **THEN** el sistema invoca `FileStoragePort.upload`, obtiene la referencia opaca, persiste la fila con esa referencia, y NO almacena el binario en la DB.

#### Scenario: Download de archivo respeta multi-tenancy
- **WHEN** un usuario FINANZAS de `tenant_A` hace `GET /api/facturas/{id}/archivo` para una factura de su tenant
- **THEN** el sistema valida `tenant_id` en el repository, invoca `FileStoragePort.download` y devuelve el binario.

#### Scenario: Download cross-tenant rechazado
- **WHEN** un usuario FINANZAS de `tenant_A` intenta `GET /api/facturas/{id}/archivo` para una factura de `tenant_B`
- **THEN** el sistema responde `404 Not Found` (el repository filtra por tenant del JWT).

---

### Requirement: Permisos `facturas:*` con fail-closed

Todos los endpoints `/api/facturas/*` SHALL aplicar `require_permission`:
- `facturas:cargar` — crear nueva factura.
- `facturas:ver` — listar y obtener detalle.
- `facturas:abonar` — transición Pendiente → Abonada.

Por defecto, FINANZAS recibe los tres; ADMIN recibe `facturas:ver`. Otros roles NO tienen acceso.

#### Scenario: Carga sin permiso rechazada
- **WHEN** un usuario COORDINADOR (sin `facturas:cargar`) hace `POST /api/facturas`
- **THEN** el sistema responde `403 Forbidden`.

#### Scenario: ADMIN solo lee
- **WHEN** un usuario ADMIN hace `POST /api/facturas/{id}/abonar`
- **THEN** el sistema responde `403 Forbidden`.

---

### Requirement: Soft delete y multi-tenancy en facturas

Todas las facturas SHALL tener `tenant_id` (filtrado por defecto en el repository) y `deleted_at` (soft delete). Ninguna factura SHALL borrarse físicamente, preservando la auditoría append-only.

#### Scenario: Soft delete preserva en audit log
- **WHEN** un usuario FINANZAS hace `DELETE /api/facturas/{id}`
- **THEN** la fila queda con `deleted_at=now`, desaparece de listados, y se registra `FACTURA_DELETE` en el audit log.

#### Scenario: Filtrado por tenant automático
- **WHEN** un usuario FINANZAS de `tenant_A` hace `GET /api/facturas`
- **THEN** el sistema devuelve únicamente facturas con `tenant_id=tenant_A AND deleted_at IS NULL`.
