## Why

C-07 establece el modelo de identidad completo de personas reales en el sistema (Usuario con PII cifrada) y el eje del modelo de autorización contextual (Asignación: quién ejerce qué rol en qué contexto académico y durante qué período). Sin estas entidades, ningún módulo posterior puede determinar qué docente tiene qué permisos sobre qué materias, lo que hace este change el desbloqueador del GATE 6 y de todos los módulos de dominio (C-08 a C-20).

## What Changes

- **Nuevo modelo `Usuario`**: extiende el modelo de auth existente (`usuarios`) con campos de PII sensible (email cifrado, DNI, CUIL, CBU, alias_cbu), datos de perfil (banco, regional, legajo, legajo_profesional, facturador) y estado (`Activo`/`Inactivo`). El campo `email` ya existía sin cifrar en C-03; esta migración lo mueve a cifrado transparente en el repositorio. El `legajo` es atributo de negocio opcional, NUNCA PK ni credencial.
- **Nuevo modelo `Asignacion`**: vincula Usuario ↔ Rol ↔ contexto académico (Materia, Carrera, Cohorte, Comisiones). Incluye `responsable_id` (jerarquía docente), rango de vigencia `desde`/`hasta` y `estado_vigencia` derivado (computado en consulta, no almacenado). La Asignación es el eje del modelo de autorización contextual del dominio.
- **Migración 006**: altera tabla `usuarios` (agrega campos PII cifrados y de perfil) + crea tabla `asignaciones`. Número 006 porque 005 fue `carrera_cohorte_materia` de C-06.
- **ABM Usuarios** (`/api/v1/admin/usuarios`): endpoints CRUD con guard `usuarios:gestionar` (solo ADMIN). La PII nunca se expone en logs ni en respuestas de listado (se devuelve enmascarada o solo el hash de verificación).
- **CRUD Asignaciones** (`/api/v1/asignaciones`): crear, listar (con filtros), obtener, actualizar vigencia, soft-delete. Guard `equipos:asignar` (COORDINADOR, ADMIN).
- **Seed RBAC**: agregar permisos `usuarios:gestionar` y `equipos:asignar` a los roles correspondientes en la migración.
- **Transparencia de cifrado en el repositorio**: `encrypt_pii`/`decrypt_pii` se aplican en el repositorio de Usuario, no en el service ni en el router. El service nunca ve texto cifrado; el router nunca ve texto plano de campos sensibles en logs.

## Capabilities

### New Capabilities

- `gestion-usuarios`: ABM de usuarios del tenant con PII cifrada (email, DNI, CUIL, CBU, alias_cbu) en reposo. Unicidad `(tenant_id, email)` enforced en service (409) + índice parcial de DB. Soft delete. Guard `usuarios:gestionar`.
- `asignaciones-rol-contexto`: CRUD de asignaciones docente ↔ rol ↔ contexto académico con vigencia temporal. `estado_vigencia` derivado del rango `desde/hasta` vs. fecha actual. Asignación vencida se conserva (histórico), no otorga permisos. Guard `equipos:asignar`.

### Modified Capabilities

- (ninguna — no hay specs existentes aún en `openspec/specs/`)

## Impact

- **Modelo existente `usuarios`**: se extiende la tabla con campos nuevos (PII cifrada + campos de perfil). El modelo ORM `Usuario` en `backend/app/models/user.py` se actualiza.
- **`backend/app/core/encryption.py`**: ya existe la utilidad `encrypt_pii`/`decrypt_pii` (AES-256-GCM). Se reutiliza directamente; no se duplica.
- **Migración 006**: `006_usuario_pii_asignacion.py` — altera `usuarios`, crea `asignaciones`, agrega permisos `usuarios:gestionar` y `equipos:asignar` al seed.
- **Archivos nuevos**: `backend/app/models/asignacion.py`, `backend/app/repositories/usuarios.py`, `backend/app/repositories/asignaciones.py`, `backend/app/services/usuarios.py`, `backend/app/services/asignaciones.py`, `backend/app/schemas/usuarios.py`, `backend/app/schemas/asignaciones.py`, `backend/app/api/v1/routers/usuarios.py`, `backend/app/api/v1/routers/asignaciones.py`.
- **Tests**: `backend/tests/test_usuarios.py`, `backend/tests/test_asignaciones.py`.
- **Dependencias desbloqueadas** cuando este change complete: C-08 (equipos-docentes), C-09 (padron-ingesta-moodle), C-13, C-14, C-15, C-16, C-18, C-19, C-20.
- **Governance**: CRÍTICO — toca identidad, multi-tenancy y PII sensible.
