# Finanzas Liquidaciones

## Purpose
View and manage teacher honorarium liquidations by period with segmented display and KPIs.

## Requirements

| ID | Requirement | Scenarios |
|---|---|---|
| R1 | Segmented Table: The UI MUST render three segments (General, NEXO, Facturantes) with subtotals per segment. | GIVEN a FINANZAS user selects cohort and month, WHEN the liquidation loads, THEN three tables appear with subtotals. GIVEN no data, WHEN the page loads, THEN empty state shows. |
| R2 | KPI Cards: The UI MUST display total_sin_factura and total_con_factura summary cards. | GIVEN a period with data, WHEN the view renders, THEN two cards show totals. |
| R3 | Close Flow: The UI MUST show a confirmation dialog before closing and disable actions after. | GIVEN an open liquidation, WHEN the user clicks Cerrar and confirms, THEN success shows and actions disable. GIVEN a closed liquidation, WHEN viewed, THEN Cerrar is disabled. |
| R4 | Historial: The UI MUST list closed liquidations with cohort and month filters. | GIVEN closed liquidations, WHEN the user applies a month filter, THEN only matching periods display. |
| R5 | Detail View: The UI MUST show teacher-level detail with base, plus, commissions, total. | GIVEN a row, WHEN the user clicks the teacher, THEN a panel shows the breakdown. |
