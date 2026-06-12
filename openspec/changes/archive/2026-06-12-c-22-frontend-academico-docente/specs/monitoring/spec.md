# Monitoring — Spec

> Tutor/Professor monitoring view with filters (student name, email, comision, regional, activity), Coordinator monitoring view with additional date range filter, and paginated results.

---

## REQ-MO-01: Tutor/Professor monitoring view with filterable, paginated table

The MonitorTable component (TUTOR/PROFESOR view) displays students assigned to the user with filterable columns and paginated results, consuming `GET /api/analisis/monitor/propio`.

### Scenarios

**Scenario 1: Monitoring data loaded with multiple pages**
GIVEN the user has the TUTOR or PROFESOR role
WHEN the user navigates to the Monitor tab
AND `GET /api/analisis/monitor/propio?page=1&page_size=50` returns results with `total > 50`
THEN a table is displayed with columns: Alumno, Email, Comisión, Regional, Actividad, Estado, Última actividad
AND the first page of 50 rows is shown
AND pagination controls are visible at the bottom showing "Página 1 de {N}"
AND a "Anterior" button (disabled on page 1) and "Siguiente" button are shown
AND the total count "Mostrando 1-50 de {total} registros" is displayed

**Scenario 2: No monitoring data**
GIVEN the user is on the Monitor tab
WHEN the endpoint returns an empty result set
THEN an empty state message "No se encontraron alumnos para los filtros seleccionados" is shown
AND the filter bar remains visible for adjustment

**Scenario 3: Filter by student name**
GIVEN the monitoring table is displayed
WHEN the user types "García" in the "Alumno" filter input
THEN `GET /api/analisis/monitor/propio` is called with `?nombre=García`
AND the table refreshes to show only matching students
AND if no match, the empty state is shown

**Scenario 4: Filter by email**
GIVEN the monitoring table is displayed
WHEN the user types an email in the "Email" filter input
THEN the query parameter `?email=...` is sent
AND the table refreshes accordingly

**Scenario 5: Filter by comision**
GIVEN the monitoring table is displayed
WHEN the user selects a comision from the "Comisión" dropdown filter
THEN the query parameter `?comision=...` is sent
AND the table refreshes

**Scenario 6: Filter by regional**
GIVEN the monitoring table is displayed
WHEN the user selects a regional from the "Regional" dropdown filter
THEN the query parameter `?regional=...` is sent
AND the table refreshes

**Scenario 7: Filter by activity**
GIVEN the monitoring table is displayed
WHEN the user selects an activity from the "Actividad" dropdown filter
THEN the query parameter `?actividad=...` is sent
AND the table refreshes

**Scenario 8: Multiple filters combined**
GIVEN the monitoring table is displayed
WHEN the user sets name="García" AND comision="Comisión A" AND regional="Regional 1"
THEN all three query parameters are sent in a single request
AND the table shows the intersection of all filters

**Scenario 9: Clear all filters**
GIVEN one or more filters are active
WHEN the user clicks "Limpiar filtros"
THEN all filter inputs are reset to their default values
AND the table refreshes with no filter parameters
AND pagination resets to page 1

**Scenario 10: Navigate to next page**
GIVEN the monitoring table has multiple pages
WHEN the user clicks "Siguiente"
THEN the component fetches `GET /api/analisis/monitor/propio?page=2&page_size=50`
AND the table displays the next page of results
AND the "Anterior" button becomes enabled

**Scenario 11: Navigate to previous page**
GIVEN the user is on page 3
WHEN the user clicks "Anterior"
THEN the component fetches page 2
AND the table updates accordingly

**Scenario 12: Loading state**
GIVEN the Monitor tab mounts or filters change
WHILE data is loading
THEN a skeleton table with placeholder rows is shown
AND pagination controls are hidden
AND filter inputs are disabled

**Scenario 13: Error loading monitoring data**
GIVEN the Monitor tab is active
WHEN the GET request fails
THEN an error message "Error al cargar los datos de monitoreo" is shown
AND a "Reintentar" button is visible
AND previous data (if any) is still visible below the error

**Scenario 14: Pagination with no results on filtered page**
GIVEN the user is on page 3 and applies a filter
WHEN the filtered result has only 1 page
THEN the pagination resets to page 1
AND the single page of results is displayed

---

## REQ-MO-02: Coordinator monitoring view adds date range filter

The MonitorTable component for COORDINADOR extends the TUTOR/PROFESOR view with a date range filter and cross-commission scope, consuming `GET /api/analisis/monitor/general`.

### Scenarios

**Scenario 1: Coordinator sees additional date range filter**
GIVEN the authenticated user has the COORDINADOR role
WHEN the user navigates to the Monitor tab
THEN all standard filters (name, email, comision, regional, activity) are visible
AND additionally, two date inputs "Fecha desde" and "Fecha hasta" are displayed in the filter bar
AND the data source is `GET /api/analisis/monitor/general` instead of `/propio`

**Scenario 2: Coordinator filters by date range**
GIVEN the Coordinator monitoring view is displayed
WHEN the user sets "Fecha desde" to 2025-03-01 and "Fecha hasta" to 2025-06-30
THEN the query parameters `?fecha_desde=2025-03-01&fecha_hasta=2025-06-30` are sent
AND the table refreshes with data in that date range

**Scenario 3: Invalid date range**
GIVEN the Coordinator monitoring view
WHEN the user sets "Fecha desde" after "Fecha hasta" (e.g., desde 2025-06-01, hasta 2025-03-01)
THEN an inline validation error "La fecha desde debe ser anterior a la fecha hasta" is shown
AND no API call is made until the user corrects the range

**Scenario 4: Clear date range filters**
GIVEN date range filters are active
WHEN the user clicks "Limpiar filtros"
THEN both date inputs are cleared
AND the query is sent without date parameters

**Scenario 5: Coordinator sees all commissions (not just own)**
GIVEN the Coordinator monitoring view
WHEN data loads
THEN results include students from ALL commissions in the tenant (not filtered by the user's own assignments)
AND the comision filter dropdown lists all available commissions

---

## REQ-MO-03: Pagination controls show current page, total pages, and page navigation

Pagination is consistent across both monitoring views and supports page-based navigation with page size of 50.

### Scenarios

**Scenario 1: Single page of results**
GIVEN the monitoring table shows results with `total <= 50`
WHEN the table renders
THEN pagination controls show "Página 1 de 1"
AND both "Anterior" and "Siguiente" buttons are disabled
AND the text "Mostrando {total} registros" is shown

**Scenario 2: Multiple pages with page navigation**
GIVEN the monitoring table shows results with `total = 134` (3 pages)
WHEN the pagination controls render
THEN "Página 1 de 3" is shown
AND "Anterior" is disabled
AND "Siguiente" is enabled
AND the text "Mostrando 1-50 de 134 registros" is displayed
WHEN the user navigates to page 2
THEN "Página 2 de 3" is shown
AND both "Anterior" and "Siguiente" are enabled
AND "Mostrando 51-100 de 134 registros" is displayed
WHEN the user navigates to page 3
THEN "Página 3 de 3" is shown
AND "Siguiente" is disabled
AND "Mostrando 101-134 de 134 registros" is displayed

**Scenario 3: Page size parameter**
GIVEN the monitoring endpoint is called
WHEN the request is sent
THEN `page_size=50` is always included in the query parameters
AND the backend returns results respecting this limit

**Scenario 4: Pagination resets on filter change**
GIVEN the user is on page 3 with no filters
WHEN the user types a name filter
THEN the page resets to 1 implicitly (the query is sent with `page=1`)
AND the filtered results show page 1
