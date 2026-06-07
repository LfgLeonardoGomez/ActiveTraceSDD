## 1. Modelo Tenant y Mixin Base

- [x] 1.1 Crear modelo SQLAlchemy `Tenant` en `backend/app/models/tenant.py` con campos: `id` (UUID PK), `nombre`, `slug` (unique), `activo`, `configuracion` (JSONB), `created_at`, `updated_at`.
- [x] 1.2 Crear `BaseModelMixin` en `backend/app/models/mixins.py` con: `id` (UUID PK), `tenant_id` (FK → tenants.id), `created_at`, `updated_at`, `deleted_at` (nullable DateTime). Usar `sqlalchemy.orm.Mapped` y tipos explícitos.
- [x] 1.3 Actualizar `backend/app/models/__init__.py` para exportar `Tenant` y `BaseModelMixin`.
- [x] 1.4 Agregar trigger/hook SQLAlchemy para auto-actualizar `updated_at` en cada `flush`/`commit`.

## 2. Utilidad de Cifrado AES-256

- [x] 2.1 Implementar `encrypt_pii(plain_text: str) -> str` en `backend/app/core/security.py` (o módulo nuevo `backend/app/core/encryption.py`) usando AES-256-GCM con nonce aleatorio de 12 bytes y salida base64 (nonce + tag + ciphertext).
- [x] 2.2 Implementar `decrypt_pii(cipher_text: str) -> str` que decodifique base64, extraiga nonce/tag/ciphertext y descifre. Lanzar error claro si falla autenticación (tamper).
- [x] 2.3 Asegurar que `ENCRYPTION_KEY` de `Settings` se use como clave de 32 bytes exactos.
- [x] 2.4 Test unitario: round-trip de cifrado/descifrado, tamper detection (modificar 1 byte del ciphertext y verificar que falla descifrado).

## 3. BaseRepository con Scope de Tenant

- [x] 3.1 Crear `BaseRepository[T]` genérico en `backend/app/repositories/base.py` que reciba `db_session` y `tenant_id` en `__init__`. Fallar con `ValueError` si `tenant_id` es `None`.
- [x] 3.2 Implementar métodos base con scope de tenant: `get_by_id`, `list`, `create`, `update`, `delete` (soft delete: set `deleted_at`).
- [x] 3.3 Aplicar filtro automático `deleted_at IS NULL` en `list` y `get_by_id`. Proveer método explícito `with_deleted()` que desactive el filtro (para casos controlados).
- [x] 3.4 Asegurar que todo query SQLAlchemy emitido por `BaseRepository` incluya `.filter(Model.tenant_id == self.tenant_id)`.
- [x] 3.5 Actualizar `backend/app/repositories/__init__.py` para exportar `BaseRepository`.

## 4. Migración Alembic 001

- [x] 4.1 Configurar entorno Alembic en `backend/alembic/` (si no existe env.py funcional post-C-01).
- [x] 4.2 Crear migración `001_tenant.py` que cree tabla `tenants` con índices: PK en `id`, UNIQUE en `slug`.
- [x] 4.3 Incluir en la migración un `op.bulk_insert` o función `seed_default_tenant()` que inserte un tenant default con slug `default` para que el sistema no arranque vacío.
- [x] 4.4 Verificar que `alembic upgrade head` ejecuta sin errores en base de test/PostgreSQL local.
- [x] 4.5 Documentar convención de naming de migraciones: `NNN_<nombre>.py`, una por change de schema.

## 5. Placeholder Modelos Core

- [x] 5.1 Crear esqueleto de modelo `Usuario` en `backend/app/models/user.py` con campos mínimos (heredando `BaseModelMixin`): `nombre`, `apellidos`, `email`, `legajo` (opcional), `estado`. Sin lógica de auth ni cifrado de PII aún (eso es C-03/C-07).
- [x] 5.2 Crear esqueleto de modelos `Rol` y `Permiso` en `backend/app/models/role.py` con campos mínimos (heredando `BaseModelMixin`). Sin matriz ni seed de datos (eso es C-04).
- [x] 5.3 Actualizar `backend/app/models/__init__.py` para exportar los nuevos modelos.
- [x] 5.4 Verificar que `Base.metadata.create_all(...)` (en tests) reconoce todas las tablas y que `tenant_id` está presente en cada una.

## 6. Tests de Dominio

- [x] 6.1 Test de aislamiento multi-tenant: crear dos registros idénticos con distinto `tenant_id` en una tabla de test; verificar que `BaseRepository` solo devuelve el del tenant scope.
- [x] 6.2 Test de soft delete: eliminar un registro vía `BaseRepository.delete()`; verificar que `deleted_at` está seteado y que `list()` no lo devuelve; verificar que `with_deleted()` sí lo devuelve.
- [x] 6.3 Test de round-trip cifrado: cifrar/decifrar cadenas de distinta longitud (email, DNI, CBU) y verificar identidad.
- [x] 6.4 Test de timestamps: crear registro y verificar `created_at` y `updated_at` no son nulos; actualizar y verificar que `updated_at` cambia.
- [x] 6.5 Test fail-closed: instanciar `BaseRepository` sin `tenant_id` y verificar que lanza `ValueError`.
- [x] 6.6 Test de seed: ejecutar migraciones y verificar que el tenant default existe con slug `default`.

## 7. Verificación y Cierre

- [x] 7.1 Ejecutar `pytest` en `backend/tests/` y asegurar ≥80% cobertura de líneas para los módulos nuevos (`models/`, `repositories/`, `core/encryption.py`).
- [x] 7.2 Ejecutar `alembic upgrade head` y `alembic downgrade -1` en base de test para verificar idempotencia.
- [x] 7.3 Verificar que no hay hard delete en ningún archivo nuevo (buscar `session.delete` o `delete()` sin soft delete).
- [x] 7.4 Verificar que todo modelo nuevo hereda de `BaseModelMixin` y tiene `tenant_id`.
- [x] 7.5 Revisar que ningún archivo supere las 500 LOC.
- [ ] 7.6 Actualizar `CHANGES.md` marcando `[x]` en `C-02` (post-implementación, no ahora).
