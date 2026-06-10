## ADDED Requirements

### Requirement: Umbral de aprobación por asignación docente
El sistema SHALL permitir al PROFESOR configurar el umbral de aprobación (porcentaje mínimo) para su asignación en una materia. El valor por defecto es 60% (RN-03).

#### Scenario: Obtener umbral vigente
- **WHEN** el PROFESOR consulta `GET /umbral/{materia_id}`
- **THEN** el sistema devuelve el `umbral_pct` configurado para la asignación activa del usuario en esa materia, o 60 si no existe configuración

#### Scenario: Configurar umbral
- **WHEN** el PROFESOR envía `PUT /umbral/{materia_id}` con `umbral_pct = 70`
- **THEN** el sistema crea o actualiza el `UmbralMateria` de la asignación del PROFESOR en esa materia con el nuevo valor

### Requirement: Umbral configura valores aprobatorios textuales
El sistema SHALL permitir al PROFESOR configurar la lista de valores textuales que cuentan como aprobado en su materia. El valor por defecto es `["Satisfactorio", "Supera lo esperado"]` (RN-02).

#### Scenario: Actualizar valores aprobatorios
- **WHEN** el PROFESOR actualiza el umbral con `valores_aprobatorios = ["Satisfactorio"]`
- **THEN** solo `"Satisfactorio"` cuenta como aprobado para las calificaciones textuales de esa asignación

### Requirement: Cambio de umbral recalcula aprobado en batch
El sistema SHALL recalcular el campo `aprobado` de todas las calificaciones del scope `(asignacion_id, materia_id)` cuando el umbral cambia, en la misma transacción.

#### Scenario: Recálculo tras cambio de umbral
- **WHEN** el PROFESOR cambia el umbral de 60% a 70%
- **THEN** todas las `Calificacion` del scope del PROFESOR en esa materia tienen su campo `aprobado` recalculado con el nuevo umbral antes de que el endpoint retorne

#### Scenario: Umbral no afecta a otros docentes
- **WHEN** el PROFESOR A cambia su umbral en la Materia M
- **THEN** las calificaciones importadas por el PROFESOR B en la misma Materia M no son recalculadas ni modificadas

### Requirement: Scope multi-tenant del umbral
El sistema SHALL filtrar el umbral por `tenant_id` en todas las consultas.

#### Scenario: Tenant isolation
- **WHEN** el PROFESOR de un tenant consulta su umbral
- **THEN** el sistema devuelve solo umbrales del tenant del usuario autenticado; nunca datos de otro tenant

### Requirement: Guard de permiso calificaciones:importar para configurar umbral
El sistema SHALL exigir `calificaciones:importar` para crear o modificar un umbral.

#### Scenario: Usuario sin permiso intenta configurar umbral
- **WHEN** un usuario sin `calificaciones:importar` intenta `PUT /umbral/{materia_id}`
- **THEN** el sistema devuelve 403 Forbidden
