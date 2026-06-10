## ADDED Requirements

### Requirement: Cliente Moodle WS con operaciones de sync
El sistema SHALL proveer un módulo `integrations/moodle_ws.py` que encapsule toda comunicación con la API de Moodle Web Services. El cliente expone al menos las operaciones: obtener usuarios inscriptos en un curso (`get_enrolled_users`) y obtener actividades de un curso (`get_course_activities`). La configuración (URL base, token) proviene de los settings del tenant.

#### Scenario: Sync on-demand exitosa
- **WHEN** un usuario con permiso `padron:cargar` llama a `POST /api/padron/moodle-sync` con `materia_id`, `cohorte_id` y `course_id`
- **THEN** el cliente obtiene los usuarios inscriptos del curso vía Moodle WS
- **AND** el sistema ejecuta el pipeline de importación (preview implícito + persist) con esos datos
- **AND** se registra `AuditLog` con acción `PADRON_CARGAR` y origen `moodle_ws`

#### Scenario: Moodle WS no configurado para el tenant
- **WHEN** se llama al endpoint de sync y el tenant no tiene `moodle_url` configurado
- **THEN** el sistema responde `422` con código `MOODLE_NOT_CONFIGURED`

---

### Requirement: Manejo de errores del WS de Moodle
El sistema SHALL mapear cualquier falla HTTP de Moodle WS a una respuesta `502 Bad Gateway` con campo `retry_after` en segundos. El error crudo de Moodle no se expone al cliente; se loggea en el sistema de observabilidad.

#### Scenario: Moodle WS responde con error HTTP
- **WHEN** el cliente Moodle recibe una respuesta con status >= 400 o un timeout
- **THEN** la operación de sync falla con error `MoodleWSError`
- **AND** el endpoint de sync responde `502` con `{"error": "MOODLE_WS_ERROR", "retry_after": 60}`
- **AND** el error detallado se loggea en formato JSON estructurado

#### Scenario: Respuesta inesperada de Moodle WS (schema inválido)
- **WHEN** el cuerpo de la respuesta de Moodle no cumple el schema esperado
- **THEN** la operación falla con `MoodleWSError` (schema mismatch)
- **AND** se loggea el detalle del error para diagnóstico

---

### Requirement: Sync nocturna deshabilitada si Moodle no está configurado
El sistema SHALL ejecutar la tarea de sync nocturna únicamente para los tenants que tengan `moodle_url` configurado. Los tenants sin configuración de Moodle no deben generar errores ni ruido en los logs por la tarea periódica.

#### Scenario: Tenant con Moodle configurado — sync nocturna
- **WHEN** el scheduler ejecuta la tarea nocturna de sync
- **THEN** se intenta sincronizar el padrón de todas las combinaciones `(materia_id, cohorte_id)` que tengan `course_id` asociado para el tenant

#### Scenario: Tenant sin Moodle configurado — sync nocturna
- **WHEN** el scheduler ejecuta la tarea nocturna de sync y el tenant no tiene `moodle_url`
- **THEN** la tarea se salta silenciosamente para ese tenant (sin error, sin log de advertencia)

---

### Requirement: Fallback a importación manual cuando Moodle WS no está disponible
El sistema SHALL funcionar completamente a través del pipeline de importación manual (upload de archivo) como path primario, independiente de si Moodle WS está configurado. La disponibilidad del cliente Moodle no es condición necesaria para ningún flujo de importación de padrón.

#### Scenario: Import manual sin Moodle configurado
- **WHEN** un usuario sube un archivo de padrón vía `POST /api/padron/preview` o `POST /api/padron/confirm`
- **AND** el tenant no tiene Moodle configurado
- **THEN** el sistema procesa el archivo correctamente sin ningún error relacionado a Moodle
