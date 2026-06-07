## Why

El sistema activia-trace es multi-tenant por diseño (ADR-002): cada institución es un tenant aislado y ningún dato puede cruzarse entre instituciones. El change C-01 sentó la infraestructura base (FastAPI, Docker, DB), pero aún no existe el modelo de datos que materialice el aislamiento de tenant. Sin la entidad `Tenant` y los mecanismos transversales de cifrado, soft delete y scoping de repositorios, no es posible construir ningún módulo de dominio posterior de forma segura. Este change es el cimiento crítico sobre el que descansan auth, RBAC, audit y todas las entidades académicas.

## What Changes

- **Modelo `Tenant`**: tabla raíz con `id` UUID, `nombre`, `slug`, `activo`, `configuracion` (JSONB opcional), timestamps.
- **Mixin base `BaseModelMixin`**: `id` UUID PK, `tenant_id` FK → Tenant, `created_at`, `updated_at`, `deleted_at` (soft delete). Aplicado a toda entidad de dominio.
- **Utilidad de cifrado AES-256**: helper `encrypt_pii` / `decrypt_pii` usando la `ENCRYPTION_KEY` de settings. Para atributos marcados `[cifrado]` (DNI, CBU, CUIL, email). Nunca texto plano en logs ni respuestas.
- **Repository genérico `BaseRepository`**: scope de tenant por defecto en **todo** query. Fail-closed: un query sin `tenant_id` explícito es un bug. Filtro de soft delete automático (`deleted_at IS NULL`) salvo override explícito.
- **Migración Alembic 001**: crea tabla `tenants` y establece convención de una migración por change de schema.
- **Placeholder de modelos core**: esqueletos de `Usuario`, `Rol`, `Permiso` (sin lógica de negocio, solo estructura ORM) para validar que el mixin y el repo base funcionan con relaciones reales.
- **Tests estrictos**: aislamiento multi-tenant (datos de tenant A no visibles para tenant B), soft delete (nunca borrado físico), round-trip de cifrado AES-256, timestamps automáticos.

## Capabilities

### New Capabilities

- `tenant-management`: modelo raíz Tenant, creación y consulta de tenants (seed inicial), configuración por tenant en JSONB.
- `multi-tenant-isolation`: mixin `tenant_id` + `BaseRepository` con scope obligatorio. Aislamiento row-level garantizado en cada query.
- `encryption-at-rest`: cifrado/descifrado AES-256 de PII. Helper reutilizable para campos `[cifrado]` en modelos futuros.
- `soft-delete`: eliminación lógica transversal vía `deleted_at`. Filtro automático en repositorios; histórico preservado.

### Modified Capabilities

- *(ninguno — este es el primer change de dominio)*

## Impact

- **Backend**: nuevos archivos en `backend/app/models/`, `backend/app/repositories/`, `backend/app/core/security.py` (cifrado), `backend/alembic/versions/001_tenant.py`.
- **Database**: nueva tabla `tenants`; convención de que toda tabla futura incluya `tenant_id` y `deleted_at`.
- **Dependencias**: requiere `C-01 foundation-setup` (ya completado). Bloquea `C-03 auth-jwt-2fa` y todo el camino crítico.
- **Seguridad**: introduce ADR-002 en código (row-level). Un bug aquí compromete todo el aislamiento multi-tenant.
