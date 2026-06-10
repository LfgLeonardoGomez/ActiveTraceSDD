## ADDED Requirements

### Requirement: Pipeline de importación en dos fases (preview + confirm)
El sistema SHALL implementar la importación de padrón en dos pasos secuenciales: (1) preview: parsea y valida el archivo retornando un resumen sin persistir nada; (2) confirm: persiste la nueva versión y desactiva la anterior. Esto garantiza que el usuario puede revisar el resultado antes de comprometerse.

#### Scenario: Preview exitoso
- **WHEN** el usuario sube un archivo válido a `POST /api/padron/preview`
- **THEN** el sistema responde con un resumen de filas válidas, filas con error, columnas detectadas y cantidad de alumnos parseados
- **AND** ningún dato se persiste en la base de datos

#### Scenario: Confirm exitoso tras preview
- **WHEN** el usuario envía `POST /api/padron/confirm` con el contenido del archivo (o referencia temporal) tras revisar el preview
- **THEN** se crea una nueva `VersionPadron` con `activa = false`
- **AND** se persisten todas las `EntradaPadron` con emails cifrados
- **AND** se activa la nueva versión (desactivando la anterior si existe)
- **AND** se registra `AuditLog` con acción `PADRON_CARGAR` y `filas_afectadas = N`

#### Scenario: Archivo con columnas faltantes
- **WHEN** el archivo subido no contiene las columnas obligatorias (`nombre`, `apellidos`, `email`)
- **THEN** el sistema responde `422 Unprocessable Entity` con detalle de columnas faltantes

#### Scenario: Archivo excede límite de tamaño
- **WHEN** el archivo supera el límite configurado (default 5 MB)
- **THEN** el sistema responde `413 Request Entity Too Large`

---

### Requirement: Formato de columnas normalizado
El sistema SHALL aceptar archivos `.xlsx` y `.csv` con las siguientes columnas (case-insensitive, espacios ignorados): `nombre`, `apellidos`, `email`, `comision`, `regional`. Las columnas `comision` y `regional` son opcionales; si no están presentes, se almacenan como cadena vacía.

#### Scenario: Columnas en mayúsculas o con espacios
- **WHEN** el archivo tiene headers como `"NOMBRE "`, `" Email"`, `"APELLIDOS"`
- **THEN** el parser los normaliza y los mapea correctamente

#### Scenario: Columna regional ausente
- **WHEN** el archivo no contiene la columna `regional`
- **THEN** el parser asigna `regional = ""` a todas las entradas

#### Scenario: Fila con email vacío
- **WHEN** una fila del archivo no tiene valor en la columna `email`
- **THEN** la fila se incluye en el resumen de errores del preview y no se persiste en confirm

---

### Requirement: Permiso granular para importar padrón
El sistema SHALL requerir el permiso `padron:cargar` para acceder a los endpoints de import. Un PROFESOR solo puede importar el padrón de materias que le están asignadas (scope `propio`). Un COORDINADOR puede importar cualquier materia del tenant.

#### Scenario: PROFESOR importa su propia materia
- **WHEN** un PROFESOR con permiso `padron:cargar` (propio) sube un archivo para una materia que le está asignada
- **THEN** el sistema procesa la importación correctamente

#### Scenario: PROFESOR intenta importar materia ajena
- **WHEN** un PROFESOR intenta importar el padrón de una materia no asignada a él
- **THEN** el sistema responde `403 Forbidden`

#### Scenario: Sin permiso padron:cargar
- **WHEN** un usuario sin permiso `padron:cargar` intenta acceder a los endpoints de import
- **THEN** el sistema responde `403 Forbidden`

---

### Requirement: Resolución de usuario_id al importar
El sistema SHALL intentar resolver el `usuario_id` de cada entrada del padrón comparando el email del archivo (descifrado) contra los emails de `Usuario` del mismo tenant. Si hay coincidencia, la `EntradaPadron` se vincula al usuario; si no, `usuario_id` queda en `null`.

#### Scenario: Resolución exitosa de usuario
- **WHEN** el email de una fila del padrón coincide con el email de un `Usuario` activo del tenant
- **THEN** la `EntradaPadron` resultante tiene `usuario_id` asignado al UUID de ese usuario

#### Scenario: Email sin usuario en el sistema
- **WHEN** el email de una fila no tiene correspondencia con ningún `Usuario` del tenant
- **THEN** la `EntradaPadron` se crea con `usuario_id = null`
- **AND** esto no genera error ni advertencia — es un estado válido
