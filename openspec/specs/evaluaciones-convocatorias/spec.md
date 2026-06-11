## ADDED Requirements

### Requirement: Crear convocatoria de evaluación
El sistema SHALL permitir a un COORDINADOR o ADMIN crear una convocatoria de evaluación (`Evaluacion`) especificando materia, cohorte, tipo, instancia, días disponibles y cupo por día. La convocatoria pertenece al tenant de la sesión activa.

#### Scenario: Crear convocatoria válida
- **WHEN** un COORDINADOR con permiso `coloquios:gestionar` envía `POST /api/coloquios/` con materia_id, cohorte_id, tipo, instancia, dias_disponibles y cupo_por_dia válidos
- **THEN** el sistema crea la convocatoria, la asocia al tenant_id de la sesión y devuelve 201 con el id generado

#### Scenario: Sin permiso coloquios:gestionar
- **WHEN** un usuario sin `coloquios:gestionar` intenta crear una convocatoria
- **THEN** el sistema devuelve 403 Forbidden

#### Scenario: Materia o cohorte de otro tenant
- **WHEN** se envía un materia_id o cohorte_id que no pertenece al tenant de la sesión
- **THEN** el sistema devuelve 404

### Requirement: Importar candidatos habilitados a una convocatoria
El sistema SHALL permitir cargar el padrón de alumnos habilitados para una convocatoria mediante `POST /api/coloquios/{id}/candidatos`. Solo alumnos en este padrón pueden reservar turno.

#### Scenario: Importar lista de candidatos
- **WHEN** un COORDINADOR con `coloquios:gestionar` envía una lista de usuario_ids válidos para una convocatoria existente
- **THEN** el sistema registra los candidatos en `evaluacion_candidato` (reemplazando si ya existían) y devuelve el count total de candidatos

#### Scenario: Convocatoria de otro tenant
- **WHEN** se intenta importar candidatos a una convocatoria de otro tenant
- **THEN** el sistema devuelve 404

### Requirement: Listar convocatorias con métricas operativas
El sistema SHALL exponer `GET /api/coloquios/` devolviendo la lista paginada de convocatorias del tenant con métricas operativas: convocados, reservas_activas, cupos_libres_por_dia.

#### Scenario: COORDINADOR lista convocatorias del tenant
- **WHEN** un COORDINADOR con `coloquios:ver` llama `GET /api/coloquios/`
- **THEN** el sistema devuelve todas las convocatorias del tenant con sus métricas calculadas al momento de la consulta

#### Scenario: PROFESOR lista convocatorias
- **WHEN** un PROFESOR con `coloquios:ver` llama `GET /api/coloquios/`
- **THEN** el sistema devuelve las convocatorias del tenant (sin restricción de titularidad — los coloquios son de la institución, no del docente)

#### Scenario: Aislamiento multi-tenant
- **WHEN** un usuario del Tenant A lista convocatorias
- **THEN** el sistema devuelve exclusivamente convocatorias del Tenant A

### Requirement: Editar convocatoria existente
El sistema SHALL permitir editar `instancia`, `dias_disponibles` y `cupo_por_dia` de una convocatoria existente vía `PATCH /api/coloquios/{id}`. No se puede cambiar `materia_id`, `cohorte_id` ni `tipo` una vez creada.

#### Scenario: Editar campos editables
- **WHEN** un COORDINADOR con `coloquios:gestionar` envía `PATCH /api/coloquios/{id}` con campos válidos
- **THEN** el sistema actualiza solo los campos editables y devuelve 200 con el recurso actualizado

#### Scenario: Intento de cambiar materia o cohorte
- **WHEN** se envía `materia_id` o `cohorte_id` en el body del PATCH
- **THEN** el sistema ignora esos campos (el schema tiene `extra='forbid'`, devuelve 422)
