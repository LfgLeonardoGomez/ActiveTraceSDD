# Grade Import — Spec

> Commission selector, file upload (CSV/XLSX), preview, activity selection, import confirmation, completion report, and clear data.

---

## REQ-GI-01: Commission selector reads materia+cohorte pairs from session

The ComisionSelector component presents a dropdown of available (materia, cohorte) pairs the user has access to, derived from the authenticated session.

### Scenarios

**Scenario 1: User has commissions assigned**
GIVEN the authenticated user has one or more commission assignments (materia + cohorte pairs)
WHEN the user opens the Comisiones section
THEN a selector dropdown shows all available pairs in format "{materia.nombre} — {cohorte.nombre}"
AND each option is selectable
AND the user sees a placeholder "Seleccioná una comisión para empezar"

**Scenario 2: No commissions assigned**
GIVEN the authenticated user has NO commission assignments
WHEN the user opens the Comisiones section
THEN a message "No tenés comisiones asignadas" is displayed
AND the selector is disabled
AND no further tabs or actions are available

**Scenario 3: Selecting a commission navigates to dashboard**
GIVEN the selector displays available commissions
WHEN the user selects a materia+cohorte pair
THEN the URL updates to `/comisiones/{materiaId}`
AND the dashboard tabs become visible for that materia
AND all subsequent API calls use the selected materiaId

**Scenario 4: Loading state**
GIVEN the user opens the Comisiones section
WHILE the session data is still resolving
THEN a centered spinner is shown
AND no selector is rendered

---

## REQ-GI-02: File upload accepts CSV or XLSX with validation

The GradeUploader component provides a file input that accepts only `.csv` and `.xlsx` extensions, with client-side validation before submission.

### Scenarios

**Scenario 1: Valid file selected**
GIVEN the commission is selected and the Importar tab is active
WHEN the user clicks the file input and selects a valid `.csv` or `.xlsx` file
THEN the file name and size (in KB) are displayed
AND an "Upload" or "Previsualizar" button becomes enabled
AND the previous status message is cleared

**Scenario 2: Invalid file type**
GIVEN the file input is visible
WHEN the user selects a file with an extension other than `.csv` or `.xlsx` (e.g., `.pdf`, `.png`)
THEN an inline error message "Formato de archivo no soportado. Usá .csv o .xlsx" is shown
AND the upload button remains disabled
AND the file is not submitted

**Scenario 3: No file selected when submitting**
GIVEN the user is on the grade upload step
WHEN the user clicks "Previsualizar" without selecting any file
THEN nothing happens (button is disabled)

**Scenario 4: File too large (implicit backend validation)**
GIVEN the user selects a file
WHEN the file size exceeds the backend limit
THEN the upload request is sent
AND if the backend returns 413 or a validation error, the error is displayed inline: "El archivo supera el tamaño máximo permitido"

---

## REQ-GI-03: Upload transitions to preview table with detected activities

On successful upload to `POST /api/v1/calificaciones/preview`, the UI transitions to a preview table showing detected activities with checkboxes for selection.

### Scenarios

**Scenario 1: Upload succeeds with detected activities**
GIVEN a valid file has been selected and the user clicked "Previsualizar"
WHEN `POST /api/v1/calificaciones/preview` returns 200 with `{ actividades: Activity[], alumnos: Alumno[] }`
THEN the upload state transitions from `uploading` to `previewing`
AND a table is displayed with columns: checkbox, activity name, type (numérica/textual), sample values (first 3 rows)
AND each row has a checkbox checked by default
AND a "Confirmar importación" button is visible
AND a "Volver" button to restart the upload is visible
AND a summary line shows "Se detectaron {N} actividades y {M} alumnos"

**Scenario 2: Upload with backend validation errors**
GIVEN the file was submitted
WHEN `POST /api/v1/calificaciones/preview` returns 422 with structured field errors (e.g., missing columns, invalid data)
THEN the UI shows an error alert with the message from the backend
AND the upload state stays at `uploading`
AND the user can reselect a different file

**Scenario 3: Network error during upload**
GIVEN the file was submitted
WHEN the request fails due to network error (timeout, connection lost)
THEN an error message "Error de conexión. Verificá tu conexión e intentá de nuevo" is shown
AND the upload state returns to `idle`
AND the file input remains populated for retry

**Scenario 4: Loading state during upload**
GIVEN the user clicked "Previsualizar"
WHILE the POST request is in flight
THEN a spinner is shown over the upload area
AND the file input and buttons are disabled
AND the text "Procesando archivo..." is displayed

---

## REQ-GI-04: Activity selection and confirm import

From the preview state, the user selects which activities to include and confirms. On confirm, `POST /api/v1/calificaciones/import` is called.

### Scenarios

**Scenario 1: Confirm import with default selection (all checked)**
GIVEN the preview table shows detected activities with all checkboxes checked
WHEN the user clicks "Confirmar importación"
THEN `POST /api/v1/calificaciones/import` is called with `{ materia_id, activities_selected: [id1, id2, ...] }`
AND the UI transitions from `previewing` to `importing`
AND a spinner is shown with "Importando calificaciones..."

**Scenario 2: Confirm import with partial selection**
GIVEN the preview table shows detected activities
WHEN the user unchecks 2 out of 5 activities
AND clicks "Confirmar importación"
THEN only the 3 checked activity IDs are sent in `activities_selected`
AND the backend only imports data for those activities

**Scenario 3: Import succeeds**
GIVEN the import request was sent
WHEN `POST /api/v1/calificaciones/import` returns 200 with `{ imported_count: 120, errors: [] }`
THEN the UI transitions to `success` state
AND a success message "{imported_count} calificaciones importadas correctamente" is shown
AND a "Ver análisis" button is visible to navigate to analytics tabs
AND the "Importar más datos" button is available to restart the flow

**Scenario 4: Import with partial errors**
GIVEN the import request was sent
WHEN the backend returns 200 with `{ imported_count: 115, errors: [{ row: 23, message: "Alumno no encontrado en padrón" }] }`
THEN the UI transitions to `success` state with a warning
AND a success message "{imported_count} calificaciones importadas" is shown
AND an expandable error list shows per-row errors
AND the errors are displayed in a collapsible section below the success message

**Scenario 5: Import fails (server error)**
GIVEN the import request was sent
WHEN the backend returns a 500 error
THEN the UI transitions to `error` state
AND an error message "Error al importar. Intentá de nuevo." is shown
AND a "Reintentar" button is visible
AND the preview table and activity selection remain visible

**Scenario 6: Uncheck all activities**
GIVEN the preview table with 3 activities
WHEN the user unchecks all checkboxes
THEN the "Confirmar importación" button becomes disabled
AND a message "Seleccioná al menos una actividad para importar" is displayed

---

## REQ-GI-05: Import completion report detects uncorrected submissions

After importing grades, the user may upload a completion report to `POST /api/v1/calificaciones/import-finalizacion` to cross-reference and detect uncorrected submissions.

### Scenarios

**Scenario 1: Upload completion report with uncorrected submissions found**
GIVEN the user has imported grades for a commission
WHEN the user uploads a completion report file
AND the backend returns `{ sin_corregir: [{ alumno, actividad, fecha_finalizacion }] }`
THEN a table is displayed with columns: Alumno, Actividad, Fecha de finalización
AND a count "Se detectaron {N} entregas sin corregir" is shown
AND an "Exportar CSV" button downloads the list via `GET /api/analisis/tps-sin-corregir/export`

**Scenario 2: No uncorrected submissions**
GIVEN the user uploads a completion report
WHEN the backend returns an empty `sin_corregir` array
THEN a success message "No se detectaron entregas sin corregir" is shown
AND the export button is shown but disabled with tooltip "Sin datos para exportar"

**Scenario 3: File validation error for completion report**
GIVEN the user selects a file for the completion report
WHEN `POST /api/v1/calificaciones/import-finalizacion` returns 422
THEN an inline error is shown with the backend message
AND the file input remains populated for retry

**Scenario 4: Loading during completion report upload**
GIVEN the user initiated the completion report upload
WHILE the request is in flight
THEN a spinner is shown over the report section
AND the file input is disabled

---

## REQ-GI-06: Clear all data for a subject with confirmation

The user can clear all imported data for the selected materia. A confirmation dialog prevents accidental deletion.

### Scenarios

**Scenario 1: Successful clear**
GIVEN the user is on any tab of the commission dashboard
WHEN the user clicks "Vaciar datos de la materia" in the settings/actions area
THEN a confirmation dialog appears with title "¿Vaciar datos de {materia}?"
AND body text "Esta acción eliminará todas las calificaciones, umbrales, y análisis de esta materia. No se puede deshacer."
AND "Cancelar" and "Confirmar vaciado" buttons
WHEN the user clicks "Confirmar vaciado"
THEN `POST /api/v1/calificaciones/vaciar` is called with `{ materia_id }`
AND on success, a toast "Datos de {materia} eliminados correctamente" is shown
AND all queries for this materiaId are invalidated via TanStack Query
AND the UI returns to the initial commission selector state

**Scenario 2: Clear cancelled**
GIVEN the confirmation dialog is open
WHEN the user clicks "Cancelar" or clicks outside the dialog
THEN the dialog closes
AND no API call is made
AND the commission state remains unchanged

**Scenario 3: Clear fails**
GIVEN the user confirmed the clear action
WHEN `POST /api/v1/calificaciones/vaciar` returns an error
THEN an error toast "Error al vaciar los datos. Intentá de nuevo." is shown
AND the dialog closes
AND the commission state remains unchanged

**Scenario 4: Loading during clear**
GIVEN the user confirmed the clear action
WHILE the POST request is in flight
THEN the "Confirmar vaciado" button shows a spinner and is disabled
AND the "Cancelar" button is disabled
AND the dialog cannot be dismissed
