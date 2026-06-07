## Context

activia-trace es una plataforma multi-tenant de gestión académica. El change anterior (`C-01 foundation-setup`) sentó la infraestructura: FastAPI async, SQLAlchemy 2.0, Alembic, PostgreSQL, Docker, OpenTelemetry, logging estructurado y health-check. Sin embargo, aún no existe ningún modelo de datos de dominio, ni mecanismo de aislamiento de tenant, ni cifrado de PII.

Este change materializa las decisiones de arquitectura ya cerradas (ADR-002 row-level multi-tenancy, ADR-001 auth propio, cifrado AES-256) en código ejecutable. Es el cimiento sobre el que descansan auth, RBAC, audit y todas las entidades académicas.

## Goals / Non-Goals

**Goals:**
1. Modelar la entidad raíz `Tenant` con campos mínimos y configuración extensible.
2. Definir un `BaseModelMixin` transversal: `id` UUID, `tenant_id`, `created_at`, `updated_at`, `deleted_at`.
3. Implementar `BaseRepository` genérico con scope de tenant obligatorio y soft delete automático.
4. Proveer helper de cifrado/descifrado AES-256 para atributos `[cifrado]`.
5. Crear la primera migración Alembic (`001_tenant`) que establece la convención de migración por change.
6. Validar el ecosistema con tests de aislamiento, soft delete y cifrado round-trip.

**Non-Goals:**
- No se implementa lógica de negocio de autenticación (login, JWT, 2FA) — eso es `C-03`.
- No se implementa RBAC ni matriz de permisos — eso es `C-04`.
- No se implementa audit log — eso es `C-05`.
- No se crean endpoints HTTP públicos para CRUD de tenants (solo seed/bootstrapping interno).
- No se soporta database-per-tenant (ADR-002 ya cerró row-level).

## Decisions

### 1. Row-level multi-tenancy con `tenant_id` en cada tabla
- **Decisión**: columna `tenant_id` FK → `tenants.id` en toda tabla de dominio. Repositorios filtran por tenant por defecto.
- **Rationale**: ADR-002 cerrado. Con un solo tenant inicial, DB-per-tenant es sobre-ingeniería. Row-level es el patrón estándar de SaaS y permite migraciones simples.
- **Alternativas consideradas**: DB-per-tenant (descartado por complejidad de migraciones, backups y pooling sin beneficio inmediato).

### 2. `BaseRepository` con scope fail-closed
- **Decisión**: todo query a través de `BaseRepository` requiere `tenant_id`. Si no se provee → `ValueError`. Filtro de soft delete (`deleted_at IS NULL`) por defecto; método explícito `with_deleted()` para overrides.
- **Rationale**: un query sin scope de tenant es un bug que debe fallar en runtime durante desarrollo/tests, no en producción. El filtro de soft delete por defecto evita filtrar datos eliminados accidentalmente.
- **Alternativas consideradas**: middleware automático de tenant (descartado porque el repository es la fuente de verdad del acceso a datos; el middleware no garantiza que queries ad-hoc o raw pasen por el filtro).

### 3. AES-256-GCM para cifrado de PII
- **Decisión**: helper `encrypt_pii(data: str) -> str` / `decrypt_pii(ciphertext: str) -> str` usando AES-256-GCM con nonce aleatorio de 12 bytes. Salida base64-encoded string que incluye nonce + tag + ciphertext.
- **Rationale**: GCM provee autenticación de integridad además de confidencialidad. El nonce se almacena junto al ciphertext (prefijo) para evitar una tabla adicional. Base64 permite almacenar en columnas `TEXT` de PostgreSQL sin problemas.
- **Alternativas consideradas**: Fernet (descartado porque usa AES-128-CBC por defecto, menos robusto); cifrado a nivel de PostgreSQL (descartado porque acopla el código al motor y dificulta testing local).

### 4. Soft delete con `deleted_at` timestamp
- **Decisión**: eliminación lógica mediante `deleted_at` (nullable `DateTime(timezone=True)`). Nunca hard delete a nivel de aplicación.
- **Rationale**: auditoría append-only requiere preservar todo registro. El timestamp permite saber cuándo se "eliminó". El mixin base lo aplica a toda entidad.
- **Alternativas consideradas**: columna `is_deleted` boolean (descartado porque pierde el momento de eliminación, útil para auditoría y retención).

### 5. UUID v4 para identidad interna
- **Decisión**: `id` UUID v4 generado por aplicación (no por BD) para toda entidad. El legajo es un atributo de negocio opcional en `Usuario` (futuro `C-07`).
- **Rationale**: evita enumeración de IDs secuenciales, facilita merge de datos entre entornos y desacopla la identidad del motor de BD.
- **Alternativas consideradas**: UUID v7 (mejor para índices B-tree, pero Python 3.13 no tiene soporte nativo en `uuid` stdlib sin librerías externas; se puede evaluar en refactor futuro).

### 6. Una migración por change de schema
- **Decisión**: cada change que altere schema genera exactamente un archivo de migración Alembic con naming `NNN_<nombre>.py`.
- **Rationale**: trazabilidad directa entre change y migración. Evita migraciones acumulativas monolíticas.
- **Alternativas consideradas**: auto-generación de migraciones por diff (descartado porque puede generar migraciones sorpresa; preferimos control manual reviewado).

## Risks / Trade-offs

- **[Risk]** Performance de cifrado/descifrado AES-256 en queries masivas → **Mitigation**: cifrar solo campos PII explícitos (DNI, CBU, CUIL, email). No cifrar todo. En queries de listado masivo, usar proyecciones que eviten descifrar campos no necesarios.
- **[Risk]** Olvido de aplicar `tenant_id` en tablas nuevas del equipo → **Mitigation**: `BaseModelMixin` obligatorio. Linters o tests de import time que verifiquen que todo modelo hereda del mixin.
- **[Risk]** `BaseRepository` muy mágico (filtro implícito) dificulta debugging → **Mitigation**: logging estructurado en modo debug que emita el `tenant_id` aplicado. Métodos explícitos `with_deleted()`, `without_tenant_scope()` (solo para casos críticos y auditados) con nombres largos y obvios.
- **[Risk]** Soft delete acumula datos "basura" → **Mitigation**: no es un riesgo real — el requisito funcional exige append-only. Si en el futuro se requiere purga, se define como proceso de archivo (no hard delete).
- **[Trade-off]** `BaseRepository` genérico sacrifica flexibilidad de SQL complejo → aceptado. Queries complejos se implementan en repositories especializados que extienden `BaseRepository` y añaden métodos concretos, manteniendo el scope de tenant base.
