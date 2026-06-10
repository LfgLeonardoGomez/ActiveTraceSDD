## Context

C-03 creó el modelo `usuarios` con campos mínimos de autenticación (email sin cifrar, password_hash, is_2fa_enabled). C-06 creó las entidades de estructura académica (Carrera, Cohorte, Materia) y el modelo de autorización RBAC (C-04). C-07 construye sobre esos cimientos para materializar el modelo de identidad completo y el eje de autorización contextual.

Estado actual del modelo `usuarios`:
- `id`, `tenant_id`, `nombre`, `apellidos`, `email` (texto plano, solo para auth), `legajo`, `estado`, `password_hash`, `is_2fa_enabled`
- El email no está cifrado — existe solo para el lookup de login, referenciado en `get_current_user`

Restricciones clave:
- La utilidad `encrypt_pii`/`decrypt_pii` (AES-256-GCM) ya existe en `backend/app/core/encryption.py`
- El `ENCRYPTION_KEY` de 32 bytes está disponible en `Settings`
- El modelo base `BaseModelMixin` ya tiene `id`, `tenant_id`, timestamps, `deleted_at`
- La migración debe ser 006 (después de 005_carrera_cohorte_materia)
- El lookup de email para auth (C-03) actualmente busca en texto plano — esto debe adaptarse para buscar por hash determinístico (HMAC-SHA256) sin romper la autenticación

## Goals / Non-Goals

**Goals:**
- Ampliar el modelo `Usuario` con todos los campos de PII cifrada (email, DNI, CUIL, CBU, alias_cbu) y campos de perfil docente
- Implementar cifrado transparente de PII en la capa de repositorio (no en service ni en router)
- Crear modelo `Asignacion` con vigencia temporal y `estado_vigencia` computado
- Exponer ABM de usuarios (`/api/v1/admin/usuarios`) con guard `usuarios:gestionar`
- Exponer CRUD de asignaciones (`/api/v1/asignaciones`) con guard `equipos:asignar`
- Agregar permisos `usuarios:gestionar` y `equipos:asignar` al seed RBAC
- Garantizar que PII nunca aparezca en logs ni en responses de listado (enmascaramiento)
- Tests con DB real (sin mocks de DB — regla dura)

**Non-Goals:**
- Autenticación de usuarios creados aquí (ya existe en C-03; el login continúa funcionando)
- Frontend de gestión de usuarios (C-21/C-23)
- Gestión de equipos docentes en bloque (clonar, asignación masiva — eso es C-08)
- Liquidaciones de usuarios (C-18)
- Perfil propio editable por el usuario (C-20)

## Decisions

### D-01: Cifrado transparente en la capa de repositorio

**Decisión**: El repositorio de `Usuario` cifra automáticamente los campos PII al escribir (`create`, `update`) y los descifra al leer (`get_by_id`, `list`). El service nunca ve texto cifrado; trabaja siempre con texto plano. El router nunca ve texto plano de PII en respuestas de listado (se enmascara o se omite).

**Alternativa considerada**: cifrar/descifrar en el service. Rechazado porque violaría el principio de que el service es lógica de negocio pura y añadiría responsabilidad de infraestructura en la capa equivocada.

**Implementación**: el repositorio de Usuario tiene un método privado `_encrypt_fields(data)` y `_decrypt_row(instance)` que transforman los campos antes/después de cada operación de DB. Los campos cifrados en la tabla son `TEXT` (base64 con nonce + tag + ciphertext).

### D-02: Búsqueda de email por hash determinístico (HMAC-SHA256)

**Decisión**: Para soportar la unicidad `(tenant_id, email)` y la búsqueda del email en login (C-03), se almacena adicionalmente una columna `email_hash` (HMAC-SHA256 del email con la `ENCRYPTION_KEY` como clave). La columna `email` contiene el ciphertext AES-256-GCM (no buscable eficientemente). El índice único parcial de unicidad se crea sobre `(tenant_id, email_hash)` WHERE `deleted_at IS NULL`.

**Alternativa considerada**: buscar todos los usuarios del tenant y descifrar uno a uno. Rechazado por ineficiencia (O(n) scans en cada login) y por ser inaceptable para tenants grandes.

**Impacto en C-03**: el `auth_service` que actualmente busca por `email` deberá actualizarse para calcular `email_hash = hmac_sha256(email, key)` y buscar por ese campo. Esta modificación se realiza dentro de este change.

**Implementación**: `hash_email_for_lookup(email: str, key: bytes) -> str` en `encryption.py` usando `hmac.new(key, email.encode(), 'sha256').hexdigest()`.

### D-03: `estado_vigencia` derivado, no almacenado

**Decisión**: `estado_vigencia` de `Asignacion` se computa como property Python en el modelo ORM (o en el schema de respuesta), no se almacena como columna. Regla: `Vigente` si `desde <= date.today() <= hasta` (o `hasta` es None), `Vencida` en cualquier otro caso.

**Alternativa considerada**: columna generada de PostgreSQL. Rechazado porque añade complejidad de migración sin beneficio real — la lógica es trivial y el cómputo no es costoso.

**Implementación**: `@property estado_vigencia` en el modelo `Asignacion` devuelve `"Vigente"` o `"Vencida"`. El schema `AsignacionRead` incluye `estado_vigencia: str` con `from_attributes=True`.

### D-04: `comisiones` como ARRAY de PostgreSQL

**Decisión**: el campo `comisiones` de `Asignacion` (lista de strings con los identificadores de comisión) se almacena como `ARRAY(Text)` de PostgreSQL. Alternativa: JSONB o tabla separada. Elegimos ARRAY porque las comisiones son simples strings sin estructura adicional, y PostgreSQL ARRAY es la solución idiomática para listas de valores simples en la misma fila.

### D-05: `responsable_id` como FK self-referencial en `asignaciones`

**Decisión**: `responsable_id` es FK de `asignaciones.id` a `usuarios.id` (no a otra asignación). Representa "el usuario coordinador que supervisa a este docente", independientemente del contexto de asignación concreto.

**Alternativa considerada**: FK de `asignacion.id` a otra `asignacion.id`. Rechazado porque haría la jerarquía dependiente del período de vigencia, cuando la relación de supervisión es entre personas, no entre asignaciones.

### D-06: Enmascaramiento de PII en responses de listado

**Decisión**: los endpoints de listado (`GET /api/v1/admin/usuarios`) devuelven los campos PII enmascarados:
- `email`: desencriptado y devuelto completo (es necesario para gestión de admins)
- `dni`, `cuil`: solo los últimos 4 caracteres (ej: `****1234`)
- `cbu`, `alias_cbu`: no devueltos en listado (solo en detalle `GET /api/v1/admin/usuarios/{id}`)

**Detalle individual**: devuelve todos los campos desencriptados al rol `usuarios:gestionar`.

**Fundamento**: balance entre usabilidad para el ADMIN y exposición mínima de PII. El ADMIN necesita identificar usuarios; no necesita ver CBU en listados masivos.

### D-07: Extensión del modelo `Usuario` vs. tabla separada

**Decisión**: los campos de PII y perfil docente se agregan a la tabla `usuarios` existente (ALTER TABLE), no en tabla separada. El modelo ORM `User` en `user.py` se actualiza para incluir los nuevos campos.

**Fundamento**: los datos son propiedades del mismo objeto de identidad. Una tabla separada añadiría complejidad de JOIN sin beneficio funcional en esta escala.

**Impacto en C-03**: el `get_current_user` en `dependencies.py` lee `user.email` — este campo cambiará de texto plano a ciphertext. El `CurrentUser.email` debe continuar siendo texto plano. El `UsuarioRepository.get_by_email_hash` se usará en el auth_service para el lookup de login.

### D-08: Migración 006 — secuencia

La migración es `006_usuario_pii_asignacion` con `down_revision = "005_carrera_cohorte_materia"`. Hace:
1. `ALTER TABLE usuarios ADD COLUMN` para cada campo nuevo (email_hash, email_cifrado renombrado desde email, dni, cuil, cbu, alias_cbu, banco, regional, legajo_profesional, facturador)
2. Migración de datos: hash de emails existentes (si los hay), cifrado del campo email existente
3. Creación de tabla `asignaciones`
4. Índices parciales de unicidad
5. Seed permisos `usuarios:gestionar` y `equipos:asignar`

**Estrategia de rollback**: el `downgrade()` revierte el ALTER TABLE, elimina la tabla asignaciones y remueve los permisos del seed.

## Risks / Trade-offs

**[Riesgo] Lookup de email en auth (C-03) se rompe si la migración no actualiza email_hash** → Mitigación: la migración incluye un paso de data-migration que calcula `email_hash` para todos los usuarios existentes. El `auth_service.py` se actualiza en este mismo change para usar `get_by_email_hash()`. Tests de regresión de login corren en este change.

**[Riesgo] La clave `ENCRYPTION_KEY` cambia en producción** → Mitigación: es un riesgo operativo fuera del scope del change. Se documenta en `ARQUITECTURA.md §9` que rotar la clave requiere re-cifrar toda la PII (operación de mantenimiento programado). No se implementa rotación automática en MVP.

**[Riesgo] `email_hash` con HMAC-SHA256 es vulnerable a rainbow tables si la clave se filtra** → Mitigación: el HMAC usa la `ENCRYPTION_KEY` de 32 bytes como secreto, lo que elimina el ataque de rainbow tables. La clave vive en variables de entorno, nunca en código ni en los logs.

**[Trade-off] Cifrado en el repositorio aumenta acoplamiento del repo a `encryption.py`** → Es aceptable: el repositorio ya tiene responsabilidad de infraestructura (SQL). El cifrado de PII es parte de los requisitos de persistencia, no de lógica de negocio.

**[Riesgo] `comisiones` como ARRAY limita filtrabilidad** → Para C-07 solo se necesita almacenar y recuperar la lista. Búsquedas por comisión específica (C-08) pueden usar `ANY(comisiones)` en PostgreSQL. Aceptable.

## Migration Plan

1. La migración 006 es aditiva: agrega columnas a `usuarios` (con `nullable=True` para datos existentes) y crea `asignaciones` como tabla nueva.
2. Data-migration inline en `upgrade()`: para usuarios existentes, calcula `email_hash = hmac_sha256(email_actual, ENCRYPTION_KEY)` y cifra `email_actual` → `email_cifrado`. Los tests pueden no tener usuarios pre-existentes, pero la migración debe ser idempotente.
3. El `auth_service.py` se actualiza en este change — no hay ventana de incompatibilidad porque es un deploy atómico.
4. Rollback: `downgrade()` revierte ALTER TABLE y elimina tabla asignaciones. Recuperable.

## Open Questions

- **OQ-C07-01**: ¿El endpoint `GET /api/v1/admin/usuarios` debe devolver el email desencriptado en el listado o solo en el detalle? → Decisión tomada en D-06: el email se devuelve en listado (el ADMIN gestiona usuarios). DNI/CUIL enmascarados en listado. CBU/alias solo en detalle.
- **OQ-C07-02**: ¿Qué pasa con el endpoint de login de C-03 que hace lookup global de email sin `tenant_id`? → Se mantiene el comportamiento actual (deuda técnica documentada en C-03). El nuevo lookup usa `email_hash` para eficiencia, pero sigue siendo global. Resolver cuando exista selector de tenant.
