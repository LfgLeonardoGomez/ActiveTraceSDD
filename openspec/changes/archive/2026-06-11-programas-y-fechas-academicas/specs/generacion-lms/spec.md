## ADDED Requirements

### Requirement: Generación de fragmento para aula virtual
El sistema SHALL generar un fragmento de contenido HTML con las fechas académicas de una materia y cohorte, listo para publicar en el aula virtual del LMS.

#### Scenario: Generación de fragmento exitosa
- **WHEN** un usuario con permiso `estructura:ver` realiza GET a `/api/fechas-academicas/<materia_id>/<cohorte_id>/lms-content`
- **THEN** el sistema retorna un string HTML con tabla de fechas (tipo, número, fecha, título)

#### Scenario: Generación sin fechas
- **WHEN** se solicita el fragmento para una materia/cohorte sin fechas registradas
- **THEN** el sistema retorna un mensaje indicando que no hay fechas configuradas
