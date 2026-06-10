# Spec: equipos-mis-teams

> Vista personal del docente sobre sus propios equipos y asignaciones.
> Todos los requisitos fueron añadidos en C-08 (equipos-docentes).

## ADDED Requirements

### Requirement: Docente ve sus propias asignaciones
El sistema MUST proveer un endpoint `GET /api/v1/equipos/mis-equipos` que retorne las asignaciones donde el `usuario_id` coincide con el ID del usuario autenticado (del JWT), dentro del tenant. El endpoint debe soportar filtros por `materia_id`, `carrera_id`, `cohorte_id` y `estado_vigencia` (Vigente / Vencida). No requiere permiso `equipos:asignar`; cualquier usuario autenticado puede acceder a su propio listado.

#### Scenario: Listado de mis equipos con filtros
- GIVEN un usuario autenticado con rol PROFESOR y 2 asignaciones vigentes
- WHEN solicita `GET /api/v1/equipos/mis-equipos?estado_vigencia=Vigente`
- THEN el sistema retorna solo las asignaciones del usuario donde estado_vigencia = "Vigente", con nombre de materia, carrera, cohorte, rol, comisiones, desde, hasta, estado_vigencia

#### Scenario: Aislamiento multi-tenant en mis-equipos
- GIVEN un usuario autenticado del tenant A
- WHEN solicita `GET /api/v1/equipos/mis-equipos`
- THEN el sistema retorna solo asignaciones del tenant A, nunca del tenant B

#### Scenario: Usuario sin asignaciones
- GIVEN un usuario autenticado sin asignaciones en el tenant
- WHEN solicita `GET /api/v1/equipos/mis-equipos`
- THEN el sistema retorna 200 con items vacío y total=0

#### Scenario: Acceso sin autenticación rechazado
- GIVEN una petición sin token válido
- WHEN solicita `GET /api/v1/equipos/mis-equipos`
- THEN el sistema retorna 401

### Requirement: Respuesta de mis-equipos incluye contexto académico denormalizado
El sistema MUST incluir en la respuesta de `mis-equipos` los nombres legibles de materia, carrera y cohorte (no solo IDs). Los campos `materia_nombre`, `carrera_nombre` y `cohorte_nombre` deben derivarse del JOIN con las tablas correspondientes, filtrado por tenant.

#### Scenario: Respuesta con nombres resueltos
- GIVEN una asignación vigente para Materia "Programación I", Carrera "TUPAD", Cohorte "MAR-2026"
- WHEN el usuario solicita `GET /api/v1/equipos/mis-equipos`
- THEN la respuesta incluye materia_nombre="Programación I", carrera_nombre="TUPAD", cohorte_nombre="MAR-2026"

#### Scenario: Asignación sin contexto académico
- GIVEN una asignación con rol ADMIN sin materia_id, carrera_id ni cohorte_id
- WHEN el usuario solicita `GET /api/v1/equipos/mis-equipos`
- THEN los campos de contexto (materia_nombre, carrera_nombre, cohorte_nombre) son null
