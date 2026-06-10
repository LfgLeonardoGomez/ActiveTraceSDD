## ADDED Requirements

### Requirement: Importar reporte de finalización de actividades
El sistema SHALL procesar el archivo de finalización exportado del LMS para detectar actividades finalizadas por el alumno pero sin calificación textual registrada (RN-07, RN-08).

#### Scenario: Actividad finalizada sin nota textual
- **WHEN** el reporte de finalización indica que un alumno completó una actividad textual y no existe `Calificacion.nota_textual` para ese alumno/actividad
- **THEN** el sistema incluye esa entrada en la lista de "posibles entregas sin corregir"

#### Scenario: Actividad numérica no incluida
- **WHEN** el reporte de finalización incluye una actividad de escala numérica finalizada sin nota
- **THEN** el sistema NO la incluye en la tabla de posibles entregas sin corregir (RN-08 — solo aplica a escala textual)

#### Scenario: Actividad ya calificada no incluida
- **WHEN** el reporte indica finalización y ya existe `Calificacion.nota_textual` para ese alumno/actividad
- **THEN** el sistema NO la incluye en la lista de posibles entregas sin corregir

### Requirement: Guard de permiso calificaciones:ver
El sistema SHALL exigir el permiso `calificaciones:ver` para acceder al resultado del reporte de finalización.

#### Scenario: Usuario sin permiso
- **WHEN** un usuario sin `calificaciones:ver` intenta acceder a los resultados del reporte de finalización
- **THEN** el sistema devuelve 403 Forbidden
