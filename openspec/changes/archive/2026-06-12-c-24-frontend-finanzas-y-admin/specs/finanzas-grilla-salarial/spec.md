# Finanzas Grilla Salarial

## Purpose
Manage SalarioBase and SalarioPlus with temporal validity.

## Requirements

| ID | Requirement | Scenarios |
|---|---|---|
| R1 | SalarioBase CRUD: The UI MUST allow create, edit, delete SalarioBase with role, amount, validity. | GIVEN a FINANZAS user, WHEN they add a SalarioBase, THEN the entry appears. GIVEN an existing entry, WHEN edited, THEN the list updates. |
| R2 | SalarioPlus CRUD: The UI MUST allow create, edit, delete SalarioPlus with group, role, amount, validity. | GIVEN a user, WHEN they add a SalarioPlus, THEN it appears in the Plus table. |
| R3 | Vigencia Conflict: The UI SHOULD display inline date-range conflicts. | GIVEN overlapping entries for the same role, WHEN the user saves, THEN an inline message appears. |
| R4 | Filters: The UI MUST filter by role and validity status. | GIVEN multiple entries, WHEN filtered by role, THEN only matching entries display. |
