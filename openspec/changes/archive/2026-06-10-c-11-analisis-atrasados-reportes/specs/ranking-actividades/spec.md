## ADDED Requirements

### Requirement: Ranking de actividades aprobadas por asignación
El sistema SHALL exponer `GET /api/analisis/ranking` que devuelva una tabla ordenada descendente por cantidad de actividades con `aprobado = True` por alumno en una asignación. Solo se incluyen alumnos con al menos una actividad aprobada (RN-09).

#### Scenario: Alumno sin actividades aprobadas excluido del ranking
- **WHEN** un alumno tiene solo `aprobado = False` o ninguna calificación en la asignación
- **THEN** el sistema NO lo incluye en el ranking

#### Scenario: Ranking ordenado descendente por actividades aprobadas
- **WHEN** se consulta el ranking de una asignación con 3 alumnos con 5, 3 y 1 actividades aprobadas respectivamente
- **THEN** el sistema devuelve los alumnos en ese orden (5 → 3 → 1)

#### Scenario: Empate en posición
- **WHEN** dos alumnos tienen el mismo número de actividades aprobadas
- **THEN** el sistema los incluye en la misma posición del ranking; el desempate secundario es alfabético por apellido

### Requirement: Scope del ranking por asignación docente
El sistema SHALL calcular el ranking exclusivamente sobre las `Calificacion` de la asignación consultada. Las calificaciones de otras asignaciones de la misma materia no se mezclan.

#### Scenario: Dos profesores en la misma materia con distintos datos
- **WHEN** el PROFESOR A y el PROFESOR B tienen calificaciones distintas en la misma materia
- **THEN** el ranking del PROFESOR A muestra solo sus datos; el del PROFESOR B, solo los suyos

### Requirement: Guard de permiso atrasados:ver en ranking
El sistema SHALL exigir `atrasados:ver` para acceder al ranking.

#### Scenario: COORDINADOR puede ver ranking de cualquier asignación del tenant
- **WHEN** un COORDINADOR con `atrasados:ver` consulta `GET /api/analisis/ranking?asignacion_id=<id>`
- **THEN** el sistema devuelve el ranking de la asignación solicitada sin restricción adicional

#### Scenario: PROFESOR solo puede ver su propio ranking
- **WHEN** un PROFESOR consulta el ranking de una asignación que no le pertenece
- **THEN** el sistema devuelve 403 Forbidden
