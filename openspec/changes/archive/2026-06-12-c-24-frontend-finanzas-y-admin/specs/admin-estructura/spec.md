# Admin Estructura

## Purpose
CRUD for Carrera, Cohorte, and Materia.

## Requirements

| ID | Requirement | Scenarios |
|---|---|---|
| R1 | Carrera CRUD: The UI MUST allow create, edit, toggle estado for Carreras. | GIVEN an ADMIN user, WHEN they add a Carrera, THEN it appears in the list. GIVEN an existing Carrera, WHEN estado toggled, THEN the list updates. |
| R2 | Cohorte CRUD: The UI MUST allow create, edit, toggle estado for Cohortes with anio and vigencia. | GIVEN an ADMIN user, WHEN they add a Cohorte, THEN it appears in the Cohortes tab. |
| R3 | Materia CRUD: The UI MUST allow create, edit, toggle estado for Materias. | GIVEN an ADMIN user, WHEN they add a Materia, THEN it appears in the Materias tab. |
| R4 | Filters: The UI MUST filter by name and estado. | GIVEN a catalog, WHEN the user searches, THEN only matching items display. |
