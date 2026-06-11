## Context

activia-trace ya cuenta con estructura académica base (Carrera, Cohorte, Materia) implementada en C-06. Los equipos docentes necesitan asociar documentos de programa y calendarizar evaluaciones por materia × cohorte. Este change es un CRUD simple con una salida adicional (generación de contenido LMS), sin lógica de negocio compleja ni integraciones externas críticas.

## Goals / Non-Goals

**Goals:**
- Modelar `ProgramaMateria` y `FechaAcademica` con scope de tenant.
- Proveer endpoints RESTful para CRUD de ambas entidades.
- Generar un fragmento HTML/texto con las fechas académicas de una materia/cohorte, listo para copiar al LMS.
- Asegurar aislamiento multi-tenant y cobertura de tests.

**Non-Goals:**
- No se implementa almacenamiento de archivos físicos (solo referencia opaca `referencia_archivo`).
- No se construye UI frontend (eso corre en C-23 / C-24).
- No se integra con Moodle WS para publicar automáticamente (solo se genera el fragmento).

## Decisions

- **Almacenamiento de archivos**: el campo `referencia_archivo` es una cadena opaca (path/ID en S3/MinIO) gestionada por un servicio de almacenamiento externo. Este change solo valida que no esté vacío en alta; la subida propiamente dicha queda fuera de scope.
- **Generación LMS**: un service `GeneracionLMSService` toma una lista de `FechaAcademica` y produce un string HTML simple con tabla de fechas. Sin lógica de template engine compleja.
- **Permisos**: gestión (`POST/PUT/DELETE`) requiere `estructura:gestionar` (ADMIN/COORDINADOR). Lectura (`GET`) disponible para cualquier rol con permiso sobre la materia/cohorte (a definir por asignación), pero dado que aún no hay matriz de permisos para lectura de materia, usamos `estructura:gestionar` para gestión y `comunicacion:enviar` (o un permiso genérico de lectura) como placeholder. **Decisión**: para lectura de fechas/programas usamos `estructura:gestionar` para simplificar, o `materias:ver` si existe. Como no existe `materias:ver`, agregamos `estructura:ver` como permiso de lectura en la matriz base (seedeo en migración). Esto mantiene fail-closed.
- **Soft delete**: ambas entidades usan soft delete (`deleted_at`) como todo el sistema.
- **Unicidad**: `ProgramaMateria` tiene unicidad `(tenant_id, materia_id, carrera_id, cohorte_id)` — un solo programa por combinación. `FechaAcademica` no tiene unicidad rígida (se permite editar fechas).

## Risks / Trade-offs

- [Riesgo] Generación LMS muy simple puede no cubrir todos los formatos de LMS → **Mitigación**: documentar que es fragmento base; personalización avanzada queda para iteración futura.
- [Riesgo] Referencia de archivo opaca sin validación de existencia → **Mitigación**: agregar nota en API docs de que la referencia debe existir en el storage configurado.

## Migration Plan

- Migración Alembic agrega tablas `programa_materia` y `fecha_academica`.
- Seed de permiso `estructura:ver` en matriz RBAC (si no existe). Dado que la matriz ya fue seedeada en C-04, agregamos en esta migración o en una nueva el permiso y su asociación a roles ADMIN/COORDINADOR/PROFESOR.
- Zero-downtime: solo agrega tablas, no altera existentes.

## Open Questions

- ¿El permiso `estructura:ver` ya existe en la matriz de C-04? Si no, lo creamos en esta migración.
