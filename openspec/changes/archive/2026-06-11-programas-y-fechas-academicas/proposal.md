## Why

El sistema necesita centralizar la gestión documental de los programas de materias y la calendarización de evaluaciones (parciales, TPs, coloquios) por materia y cohorte. Sin esta capacidad, los equipos docentes no disponen de una fuente única de verdad para los programas vigentes ni para las fechas de evaluación, lo que dificulta la planificación académica y la generación de contenido para el aula virtual.

## What Changes

- Introducir el modelo `ProgramaMateria` para asociar documentos oficiales de programa a una combinación materia × carrera × cohorte.
- Introducir el modelo `FechaAcademica` para registrar fechas de evaluaciones (parcial, TP, coloquio, recuperatorio) con número de instancia y período.
- Endpoints REST para CRUD de programas y fechas académicas, con scope de tenant y permisos finos.
- Generación de fragmento de contenido listo para el aula virtual del LMS (a partir de fechas académicas).
- Migraciones de base de datos para las nuevas tablas.
- Tests de cobertura para CRUD, aislamiento multi-tenant, y generación de contenido LMS.

## Capabilities

### New Capabilities
- `programa-materia`: gestión de documentos oficiales de programas por materia, carrera y cohorte.
- `fecha-academica`: calendarización de evaluaciones (parciales, TPs, coloquios, recuperatorios) con número de instancia y período académico.
- `generacion-lms`: generación de fragmento de contenido formateado para publicar en el aula virtual del LMS.

### Modified Capabilities
- (sin modificaciones a capabilities existentes)

## Impact

- Backend: nuevos modelos SQLAlchemy, repositories, services, routers.
- API: nuevos endpoints bajo `/api/programas` y `/api/fechas-academicas`.
- Base de datos: migración Alembic para `programa_materia` y `fecha_academica`.
- RBAC: requiere permisos `estructura:gestionar` para gestión; lectura disponible para roles con acceso a la materia/cohorte.
- Audit: operaciones de alta/modificación/baja generan registros de auditoría.
