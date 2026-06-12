# Finanzas Facturas

## Purpose
Manage invoices from independent teachers.

## Requirements

| ID | Requirement | Scenarios |
|---|---|---|
| R1 | Invoice List: The UI MUST list invoices with teacher, period, status, amount. | GIVEN a FINANZAS user, WHEN the page loads, THEN a table shows invoices with status badges. |
| R2 | Status Toggle: The UI MUST allow marking an invoice as Abonada. | GIVEN a pending invoice, WHEN the user clicks Abonar, THEN status updates to Abonada. |
| R3 | Detail: The UI MUST show invoice metadata including file and payment date. | GIVEN an invoice row, WHEN the user clicks detail, THEN a panel shows metadata. |
| R4 | Separation: The UI MUST exclude facturantes from the liquidation total. | GIVEN a facturante, WHEN viewing liquidation, THEN they appear in Facturantes segment only. |
