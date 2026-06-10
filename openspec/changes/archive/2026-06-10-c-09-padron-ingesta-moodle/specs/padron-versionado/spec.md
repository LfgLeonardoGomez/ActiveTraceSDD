## ADDED Requirements

### Requirement: Modelo de padrón versionado por materia y cohorte
El sistema SHALL mantener un historial de versiones del padrón de alumnos por combinación `(tenant_id, materia_id, cohorte_id)`. Cada carga genera una nueva `VersionPadron`; la activación de una nueva versión desactiva la anterior sin borrarla. Solo puede existir una versión `activa = true` por combinación en simultáneo.

#### Scenario: Activar nueva versión desactiva la anterior
- **WHEN** se confirma la importación de un nuevo padrón para `(materia_id, cohorte_id)`
- **THEN** la versión previamente activa pasa a `activa = false`
- **AND** la nueva versión queda con `activa = true`
- **AND** ambas versiones persisten en la base de datos (no se borra la anterior)

#### Scenario: No existe versión previa
- **WHEN** se importa el primer padrón para una combinación `(materia_id, cohorte_id)` sin historial previo
- **THEN** la nueva versión queda como la única y con `activa = true`

#### Scenario: Aislamiento multi-tenant
- **WHEN** el tenant A activa una versión de padrón para `materia_id = X`
- **THEN** los datos del tenant B con el mismo `materia_id = X` no se ven afectados

---

### Requirement: EntradaPadron con email cifrado
El sistema SHALL almacenar el campo `email` de cada `EntradaPadron` cifrado en reposo (AES-256), de forma consistente con el cifrado de `Usuario.email`. El email en claro nunca debe aparecer en logs ni en respuestas de API que no sean de consulta explícita por el propietario del dato.

#### Scenario: Email cifrado al persistir
- **WHEN** se persiste una `EntradaPadron` con un email en claro
- **THEN** el valor almacenado en la columna `email` de la base de datos está cifrado

#### Scenario: Email descifrado al leer
- **WHEN** el service recupera una `EntradaPadron` para mostrarla al usuario autorizado
- **THEN** el email se devuelve descifrado en la respuesta

#### Scenario: Email no expuesto en logs
- **WHEN** el sistema registra una acción de auditoría `PADRON_CARGAR`
- **THEN** el campo `detalle` del `AuditLog` no contiene ningún email en claro

---

### Requirement: EntradaPadron puede existir sin usuario registrado
El sistema SHALL permitir que una `EntradaPadron` exista con `usuario_id = null`, representando un alumno que aún no tiene cuenta en el sistema. El nombre y apellidos se almacenan desnormalizados para preservar el histórico.

#### Scenario: Entrada sin cuenta de usuario
- **WHEN** se importa un padrón con un alumno cuyo email no corresponde a ningún `Usuario` del tenant
- **THEN** se crea la `EntradaPadron` con `usuario_id = null` y los campos `nombre`, `apellidos`, `email` (cifrado) tomados del archivo

#### Scenario: Entrada con cuenta de usuario existente
- **WHEN** se importa un padrón con un alumno cuyo email coincide con un `Usuario.email` del tenant
- **THEN** se crea la `EntradaPadron` con `usuario_id` resuelto al UUID del usuario correspondiente

---

### Requirement: Vaciar padrón de una materia es scope-isolated
El sistema SHALL permitir vaciar todos los datos de padrón de una materia únicamente dentro del scope del usuario que ejecuta la operación (RN-04). La operación elimina todas las versiones (activas e inactivas) de padrón asociadas a `(usuario/asignacion × materia_id)`. No afecta datos de otros docentes en la misma materia.

#### Scenario: Vaciado de padrón propio
- **WHEN** un PROFESOR ejecuta `DELETE /api/padron/{materia_id}` sobre una materia asignada a él
- **THEN** se eliminan (soft delete) todas las `VersionPadron` y sus `EntradaPadron` asociadas a esa materia en el scope del profesor
- **AND** el padrón de otros docentes en la misma materia no se ve afectado

#### Scenario: Intento de vaciado fuera del scope
- **WHEN** un PROFESOR intenta vaciar el padrón de una materia no asignada a él
- **THEN** el sistema responde `403 Forbidden`
