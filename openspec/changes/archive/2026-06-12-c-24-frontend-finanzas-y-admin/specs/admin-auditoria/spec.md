# Admin Auditoria

## Purpose
Audit panel with charts and filterable log.

## Requirements

| ID | Requirement | Scenarios |
|---|---|---|
| R1 | Actions Chart: The UI MUST display actions per day. | GIVEN an ADMIN or COORDINADOR, WHEN the panel loads, THEN a line chart shows daily counts. |
| R2 | Communications Chart: The UI MUST display communication status by teacher. | GIVEN a user, WHEN the panel loads, THEN a stacked bar shows statuses per teacher. |
| R3 | Interactions Chart: The UI MUST display interactions by teacher and materia. | GIVEN a user, WHEN the panel loads, THEN a chart shows metrics per teacher and materia. |
| R4 | Audit Log: The UI MUST show a paginated log with filters for date, materia, user, status. | GIVEN an ADMIN, WHEN a date filter is applied, THEN matching entries display. GIVEN a COORDINADOR, WHEN viewing the log, THEN only propio scope entries display. |
| R5 | Scope Badge: The UI MUST show "Vista personal" when COORDINADOR sees propio scope. | GIVEN a COORDINADOR, WHEN the panel loads, THEN a badge indicates restricted scope. |
