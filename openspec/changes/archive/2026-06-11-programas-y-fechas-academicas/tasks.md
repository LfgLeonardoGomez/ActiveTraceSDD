## 1. Base de datos y modelos

- [x] 1.1 Crear migración Alembic para `programa_materia` (id, tenant_id, materia_id, carrera_id, cohorte_id, titulo, referencia_archivo, cargado_at, created_at, updated_at, deleted_at)
- [x] 1.2 Crear migración Alembic para `fecha_academica` (id, tenant_id, materia_id, cohorte_id, tipo, numero, periodo, fecha, titulo, created_at, updated_at, deleted_at)
- [x] 1.3 Crear modelo SQLAlchemy `ProgramaMateria` con mixin base, soft delete, FKs a Materia/Carrera/Cohorte
- [x] 1.4 Crear modelo SQLAlchemy `FechaAcademica` con mixin base, soft delete, FKs a Materia/Cohorte
- [x] 1.5 Agregar permiso `estructura:ver` y asociaciones en matriz RBAC (seed en migración si no existe)

## 2. Repositories

- [x] 2.1 Crear `ProgramaMateriaRepository` con métodos: create, get_by_id, list_by_materia, update, soft_delete, count_by_combinacion (para unicidad)
- [x] 2.2 Crear `FechaAcademicaRepository` con métodos: create, get_by_id, list_by_materia, list_by_materia_cohorte, update, soft_delete
- [x] 2.3 Asegurar que todos los queries filtran por `tenant_id` por defecto

## 3. Schemas Pydantic

- [x] 3.1 Crear `ProgramaMateriaCreateSchema`, `ProgramaMateriaUpdateSchema`, `ProgramaMateriaResponseSchema` con `extra='forbid'`
- [x] 3.2 Crear `FechaAcademicaCreateSchema`, `FechaAcademicaUpdateSchema`, `FechaAcademicaResponseSchema` con `extra='forbid'`
- [x] 3.3 Crear `LMSContentResponseSchema` para la salida de generación LMS

## 4. Services

- [x] 4.1 Crear `ProgramaMateriaService` con CRUD + validación de unicidad (materia×carrera×cohorte)
- [x] 4.2 Crear `FechaAcademicaService` con CRUD + listado ordenado
- [x] 4.3 Crear `GeneracionLMSService` que reciba `materia_id` + `cohorte_id` y genere HTML de tabla de fechas
- [x] 4.4 Agregar auditoría en operaciones de alta/modificación/baja (llamadas a AuditLog)

## 5. Routers y endpoints

- [x] 5.1 Crear router `/api/programas` con POST, GET (list), GET by id, PUT, DELETE; guard `estructura:gestionar` para mutaciones, `estructura:ver` para lectura
- [x] 5.2 Crear router `/api/fechas-academicas` con POST, GET (list), GET by id, PUT, DELETE; mismos guards
- [x] 5.3 Crear endpoint GET `/api/fechas-academicas/{materia_id}/{cohorte_id}/lms-content` con guard `estructura:ver`
- [x] 5.4 Registrar ambos routers en `app/main.py`

## 6. Tests

- [x] 6.1 Test de alta de programa (éxito y conflicto de unicidad)
- [x] 6.2 Test de CRUD completo de fecha académica
- [x] 6.3 Test de aislamiento multi-tenant (un tenant no ve datos de otro)
- [x] 6.4 Test de generación LMS con y sin fechas
- [x] 6.5 Test de soft delete en ambas entidades
- [x] 6.6 Test de permisos (sin `estructura:gestionar` → 403 en mutaciones)
- [x] 6.7 Verificar cobertura ≥80% líneas, ≥90% reglas de negocio

## 7. Documentación y cierre

- [x] 7.1 Actualizar `CHANGES.md` marcando `[x]` C-17
- [x] 7.2 Archivar change con `/opsx:archive`
