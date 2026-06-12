# Analytics — Spec

> Threshold configuration, at-risk students view, ranking, quick reports (KPI cards), final grades table + CSV export, uncorrected TPs table + CSV export. All with loading, empty, and error states.

---

## REQ-AN-01: Threshold configuration reads current value and saves via slider

The ThresholdEditor component fetches the current threshold value from `GET /api/v1/umbral/{materia_id}`, displays it as a percentage slider, and persists changes via `PUT /api/v1/umbral/{materia_id}`.

### Scenarios

**Scenario 1: Load threshold value successfully**
GIVEN the user is on the Umbral tab with a selected materia
WHEN the component mounts
THEN `GET /api/v1/umbral/{materia_id}` is called
AND on success, a slider input is displayed showing the current value as a percentage (default 60%)
AND the value is shown as both a number input and a textual label "{value}%"
AND a "Guardar" button is present but disabled (no changes yet)

**Scenario 2: Edit threshold value**
GIVEN the threshold slider displays the current value
WHEN the user moves the slider to 75%
THEN the display updates in real-time to show "75%"
AND the "Guardar" button becomes enabled
AND a "Cancelar" button appears to reset to the original value

**Scenario 3: Save threshold value successfully**
GIVEN the user has changed the threshold to 75%
WHEN the user clicks "Guardar"
THEN `PUT /api/v1/umbral/{materia_id}` is called with `{ umbral: 75 }`
AND on success, a toast "Umbral actualizado a 75%" is shown
AND the "Guardar" button becomes disabled again
AND the new value is reflected as the current value

**Scenario 4: Save threshold fails**
GIVEN the user has changed the threshold and clicks "Guardar"
WHEN `PUT /api/v1/umbral/{materia_id}` returns an error
THEN an error toast "Error al guardar el umbral. Intentá de nuevo." is shown
AND the slider remains at the edited value (not reverted)
AND the "Guardar" button remains enabled for retry

**Scenario 5: Cancel edit reverts to original value**
GIVEN the user changed the slider to 75%
WHEN the user clicks "Cancelar"
THEN the slider snaps back to the previously saved value
AND the "Guardar" button becomes disabled again
AND the "Cancelar" button disappears

**Scenario 6: Loading state for threshold**
GIVEN the Umbral tab mounts
WHILE `GET /api/v1/umbral/{materia_id}` is in flight
THEN a skeleton/spinner is shown where the slider would be
AND the slider is not rendered

**Scenario 7: Error loading threshold**
GIVEN the Umbral tab mounts
WHEN `GET /api/v1/umbral/{materia_id}` fails (network error or 500)
THEN an error message "Error al cargar el umbral" is shown
AND a "Reintentar" button retries the GET request

---

## REQ-AN-02: At-risk students view shows sortable, selectable table

The AtrasadosTable component displays at-risk students for the selected materia, computed against the configured threshold. Students can be selected for communication targeting.

### Scenarios

**Scenario 1: At-risk students loaded successfully**
GIVEN the user is on the Atrasados tab
WHEN `GET /api/analisis/atrasados?materia_id={materia_id}` returns data
THEN a table is displayed with columns: checkbox, Alumno, Email, Actividades faltantes, Nota promedio, Estado
AND each row has a checkbox for selection
AND the table is sortable by clicking any column header (toggles asc/desc)
AND a count "Se detectaron {N} alumnos atrasados" is shown above the table

**Scenario 2: No at-risk students**
GIVEN the user is on the Atrasados tab
WHEN `GET /api/analisis/atrasados?materia_id={materia_id}` returns an empty array
THEN a message "No hay alumnos atrasados en esta comisión" is displayed
AND a success-style illustration or icon is shown
AND the table is not rendered

**Scenario 3: Select individual at-risk student**
GIVEN the at-risk students table is displayed
WHEN the user checks the checkbox for one student
THEN the row is visually highlighted (selected state)
AND a floating action bar appears with "Comunicar seleccionados ({count})" button

**Scenario 4: Select all at-risk students**
GIVEN the at-risk students table is displayed
WHEN the user checks the header checkbox
THEN all rows become checked
AND the action bar shows "Comunicar seleccionados ({total})"

**Scenario 5: Deselect all**
GIVEN some or all rows are selected
WHEN the user unchecks the header checkbox
THEN all rows become unchecked
AND the action bar disappears

**Scenario 6: Loading state**
GIVEN the user is on the Atrasados tab
WHILE `GET /api/analisis/atrasados?materia_id={materia_id}` is in flight
THEN a skeleton table with 5 placeholder rows is shown
AND no action bar is rendered

**Scenario 7: Error loading at-risk students**
GIVEN the user is on the Atrasados tab
WHEN the GET request fails
THEN an error message "Error al cargar los alumnos atrasados" is shown
AND a "Reintentar" button is visible

**Scenario 8: Filter by student name**
GIVEN the at-risk students table is displayed
WHEN the user types a name in the search input above the table
THEN the table filters to show only students whose name matches the search term (case-insensitive, partial match)
AND the count updates to reflect filtered results
AND if no match is found, a message "No hay resultados para '{search}'" is shown

---

## REQ-AN-03: Ranking of approved activities displays ordered table

The RankingTable component shows students ordered by number of approved activities, descending.

### Scenarios

**Scenario 1: Ranking loaded successfully**
GIVEN the user is on the Ranking tab
WHEN `GET /api/analisis/ranking?materia_id={materia_id}` returns data
THEN a table is displayed with columns: Posición, Alumno, Actividades aprobadas, Total actividades, Porcentaje
AND rows are ordered by approved count descending
AND position numbers are displayed (1, 2, 3, ...)
AND the top 3 positions have distinct visual styling (gold/silver/bronze)

**Scenario 2: Ranking empty (no activities imported)**
GIVEN the user is on the Ranking tab
WHEN the endpoint returns an empty array
THEN an empty state message "No hay actividades importadas para mostrar ranking" is shown
AND a prompt to go to the import tab is displayed as a link/button

**Scenario 3: Loading state**
GIVEN the user is on the Ranking tab
WHILE data is loading
THEN a skeleton table with placeholder rows is shown

**Scenario 4: Error loading ranking**
GIVEN the user is on the Ranking tab
WHEN the GET request fails
THEN an error message "Error al cargar el ranking" is shown
AND a "Reintentar" button is visible

---

## REQ-AN-04: Quick reports show KPI cards for the commission

The ReportesSummary component displays aggregate KPIs in a card grid layout.

### Scenarios

**Scenario 1: KPI cards loaded with data**
GIVEN the user is on the Reportes tab
WHEN `GET /api/analisis/reporte-rapido?materia_id={materia_id}` returns `{ total_alumnos, con_aprobadas, atrasados, pct_aprobacion }`
THEN a grid of KPI cards is displayed:
- "Total alumnos" card shows total_alumnos
- "Con al menos una aprobada" card shows con_aprobadas
- "Atrasados" card shows atrasados (with warning icon if > 0)
- "Porcentaje de aprobación" card shows "pct_aprobacion%" (color-coded: green ≥ 70%, yellow ≥ 40%, red < 40%)

**Scenario 2: No data available (sin_datos=true)**
GIVEN the user is on the Reportes tab
WHEN the endpoint returns `{ sin_datos: true, ... }` with all zeros
THEN an empty state message "No hay datos de esta comisión. Importá calificaciones para ver reportes." is shown
AND no KPI cards are rendered

**Scenario 3: Loading state**
GIVEN the user is on the Reportes tab
WHILE data is loading
THEN 4 skeleton cards are shown in the grid layout

**Scenario 4: Error loading report**
GIVEN the user is on the Reportes tab
WHEN the GET request fails
THEN an error message "Error al cargar los reportes" is shown
AND a "Reintentar" button is visible

---

## REQ-AN-05: Final grades view with table and CSV export

The NotasFinalesTable component displays calculated final grades per student with an export button that triggers a CSV file download.

### Scenarios

**Scenario 1: Final grades loaded with data**
GIVEN the user is on the Notas finales tab
WHEN `GET /api/analisis/notas-finales?materia_id={materia_id}` returns data
THEN a table is displayed with columns: Alumno, Email, Nota final, Estado (Aprobado/Desaprobado)
AND each row shows nota_final with 2 decimal places
AND the Estado column shows "Aprobado" in green if >= threshold, "Desaprobado" in red if below
AND an "Exportar CSV" button is visible above the table

**Scenario 2: Export CSV triggers file download**
GIVEN the final grades table is displayed
WHEN the user clicks "Exportar CSV"
THEN `GET /api/analisis/notas-finales/export?materia_id={materia_id}` is called
AND the browser downloads a file named `notas_finales_{materia}.csv`
AND a toast "Descarga iniciada" is shown

**Scenario 3: No final grades data**
GIVEN the user is on the Notas finales tab
WHEN the endpoint returns an empty array
THEN an empty state message "No hay notas finales para mostrar. Importá calificaciones primero." is shown
AND the export button is disabled with tooltip "Sin datos para exportar"

**Scenario 4: Loading state for final grades**
GIVEN the user is on the Notas finales tab
WHILE data is loading
THEN a skeleton table with placeholder rows is shown
AND the export button shows a spinner

**Scenario 5: Error loading final grades**
GIVEN the user is on the Notas finales tab
WHEN the GET request fails
THEN an error message "Error al cargar las notas finales" is shown
AND a "Reintentar" button is visible

**Scenario 6: Export fails (network error)**
GIVEN the user clicked "Exportar CSV"
WHEN the download request fails
THEN an error toast "Error al descargar el archivo. Intentá de nuevo." is shown

---

## REQ-AN-06: Uncorrected TPs view with table and CSV export

The TpsSinCorregirTable component displays submissions that are finalized but uncorrected, with an export button.

### Scenarios

**Scenario 1: Uncorrected TPs loaded with data**
GIVEN the user has imported a completion report
WHEN the user navigates to the TPs sin corregir tab
AND the backend returns uncorrected submission data
THEN a table is displayed with columns: Alumno, Email, Actividad, Fecha de finalización
AND a count "Se detectaron {N} entregas sin corregir" is shown
AND an "Exportar CSV" button is visible

**Scenario 2: No uncorrected TPs**
GIVEN the user navigates to the TPs sin corregir tab
WHEN no uncorrected submissions exist
THEN a message "No hay trabajos prácticos sin corregir" is shown
AND the export button is disabled with tooltip "Sin datos para exportar"

**Scenario 3: Loading state**
GIVEN the user navigates to the TPs sin corregir tab
WHILE data is loading
THEN a skeleton table is shown

**Scenario 4: Error loading uncorrected TPs**
GIVEN the user navigates to the TPs sin corregir tab
WHEN the GET request fails
THEN an error message "Error al cargar los trabajos sin corregir" is shown
AND a "Reintentar" button is visible

**Scenario 5: Export CSV for uncorrected TPs**
GIVEN the table has data
WHEN the user clicks "Exportar CSV"
THEN `GET /api/analisis/tps-sin-corregir/export?materia_id={materia_id}` is called
AND the browser downloads `tps_sin_corregir_{materia}.csv`
AND a toast "Descarga iniciada" is shown
