## ADDED Requirements

### Requirement: Detectar columnas de nota numérica en archivo LMS
El sistema SHALL identificar como columnas de nota numérica aquellas cuyo encabezado termine en `(Real)` (RN-01). Cualquier otra columna no se procesa como nota numérica.

#### Scenario: Columna numérica detectada
- **WHEN** el archivo contiene una columna con encabezado `"Actividad 1 (Real)"`
- **THEN** el sistema la incluye en la lista de actividades detectadas con tipo `numerica`

#### Scenario: Columna sin sufijo ignorada
- **WHEN** el archivo contiene una columna `"Actividad 1 (Calificación del foro)"` sin el sufijo `(Real)`
- **THEN** el sistema NO la incluye como actividad numérica

### Requirement: Detectar columnas de nota textual en archivo LMS
El sistema SHALL identificar columnas de escala textual cuyos valores sean `"Satisfactorio"`, `"Supera lo esperado"`, `"No satisfactorio"`, `"No alcanzado"` u otros valores del conjunto configurable (RN-02).

#### Scenario: Columna textual detectada
- **WHEN** el archivo contiene una columna con al menos un valor del conjunto aprobatorio o no aprobatorio configurado
- **THEN** el sistema la incluye en la lista de actividades detectadas con tipo `textual`

### Requirement: Vista previa de importación sin persistir
El sistema SHALL generar una vista previa de las actividades y alumnos detectados en el archivo sin persistir ningún dato.

#### Scenario: Preview exitoso
- **WHEN** el PROFESOR sube un archivo LMS válido al endpoint `POST /calificaciones/preview`
- **THEN** el sistema devuelve la lista de actividades detectadas (nombre, tipo, cantidad de registros) y los alumnos identificados sin escribir en la base de datos

#### Scenario: Archivo inválido o sin columnas detectables
- **WHEN** el archivo subido no tiene columnas con el sufijo `(Real)` ni columnas textuales reconocibles
- **THEN** el sistema devuelve un error 422 indicando que no se detectaron actividades válidas

### Requirement: Confirmación e importación de calificaciones
El sistema SHALL persistir las calificaciones seleccionadas tras la confirmación del PROFESOR, calculando `aprobado` según el umbral vigente de esa asignación (RN-01, RN-02, RN-03).

#### Scenario: Importación con actividades seleccionadas
- **WHEN** el PROFESOR confirma la importación con una selección de actividades sobre un archivo válido
- **THEN** el sistema persiste solo las calificaciones de las actividades seleccionadas, calcula `aprobado` para cada fila y registra el evento `CALIFICACIONES_IMPORTAR` en auditoría

#### Scenario: Derivación de aprobado con nota numérica
- **WHEN** una calificación tiene `nota_numerica` y existe umbral configurado para la asignación
- **THEN** `aprobado = nota_numerica >= (nota_maxima * umbral_pct / 100)`

#### Scenario: Derivación de aprobado con nota textual aprobatoria
- **WHEN** una calificación tiene `nota_textual = "Satisfactorio"` (o cualquier valor de `valores_aprobatorios`)
- **THEN** `aprobado = True`

#### Scenario: Derivación de aprobado con nota textual no aprobatoria
- **WHEN** una calificación tiene `nota_textual = "No satisfactorio"` (valor no presente en `valores_aprobatorios`)
- **THEN** `aprobado = False`

#### Scenario: Sin umbral configurado — usa defecto 60%
- **WHEN** no existe `UmbralMateria` para la asignación y se importan notas numéricas
- **THEN** el sistema usa `umbral_pct = 60` como valor por defecto

### Requirement: Scope aislado por docente en importación
El sistema SHALL aislar las calificaciones importadas por el scope `(usuario_id × materia_id)`. La importación de un docente no afecta los datos de otro docente en la misma materia (RN-04).

#### Scenario: Dos docentes en la misma materia
- **WHEN** el PROFESOR A importa calificaciones en la Materia M
- **THEN** el PROFESOR B en la misma Materia M no ve ni pierde sus calificaciones previas

### Requirement: Vaciar calificaciones de una materia
El sistema SHALL permitir al PROFESOR eliminar (soft delete) todas sus calificaciones en una materia sin afectar las de otros docentes (RN-04).

#### Scenario: Vaciado scope-isolated
- **WHEN** el PROFESOR ejecuta `DELETE /calificaciones/{materia_id}`
- **THEN** solo las calificaciones del scope `(usuario_activo, materia_id)` quedan marcadas como eliminadas; las de otros docentes no se ven afectadas

### Requirement: Guard de permiso calificaciones:importar
El sistema SHALL exigir el permiso `calificaciones:importar` en los endpoints de preview, importación y vaciado.

#### Scenario: Usuario sin permiso
- **WHEN** un usuario sin `calificaciones:importar` intenta acceder a `POST /calificaciones/import`
- **THEN** el sistema devuelve 403 Forbidden
