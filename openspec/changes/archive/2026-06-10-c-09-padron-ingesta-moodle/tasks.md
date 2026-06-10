## 1. Migración y modelos

- [x] 1.1 Crear modelos SQLAlchemy `VersionPadron` y `EntradaPadron` en `app/models/padron.py` con todos los campos del E6 (incluido `email` como columna cifrada, `usuario_id` nullable)
- [x] 1.2 Agregar la propiedad `email` con cifrado AES-256 en `EntradaPadron` usando el helper de cifrado de C-02 (mismo patrón que `Usuario.email`)
- [x] 1.3 Escribir migración Alembic `006_padron.py`: tablas `version_padron` y `entrada_padron` con índice `(tenant_id, materia_id, cohorte_id, activa)` para lookup eficiente de versión activa
- [x] 1.4 Crear schemas Pydantic v2 (`extra='forbid'`): `VersionPadronRead`, `EntradaPadronRead`, `PadronPreviewResponse`, `PadronConfirmRequest`, `PadronImportRow`

## 2. Repository

- [x] 2.1 Crear `app/repositories/padron_repository.py` con `PadronRepository` que extiende el repositorio genérico: todo query filtra por `tenant_id` por defecto
- [x] 2.2 Implementar `get_active_version(materia_id, cohorte_id) → VersionPadron | None`
- [x] 2.3 Implementar `activate_version(new_version_id, materia_id, cohorte_id)`: en una transacción, desactiva la versión previa y activa la nueva (garantiza solo 1 activa)
- [x] 2.4 Implementar `get_entradas_by_version(version_id) → list[EntradaPadron]`
- [x] 2.5 Escribir tests unitarios del repository: aislamiento multi-tenant (tenant B no ve datos de tenant A), swap de versión activa, lookup de versión activa cuando no existe ninguna

## 3. Service de importación

- [x] 3.1 Crear `app/services/padron_service.py`
- [x] 3.2 Escribir tests primero (TDD): test de parse de xlsx con columnas válidas, test de columnas faltantes → 422, test de fila con email vacío → error en preview, test de resolución de `usuario_id` (email con y sin match)
- [x] 3.3 Implementar `parse_file(file_content, filename) → list[PadronImportRow]`: acepta `.xlsx` y `.csv`; normaliza headers (strip + lower); detecta columnas faltantes; filtra filas con email vacío con mensaje de error
- [x] 3.4 Implementar `generate_preview(rows, materia_id, cohorte_id, tenant_id) → PadronPreviewResponse`: cuenta filas válidas/errores, muestra columnas detectadas, no persiste nada
- [x] 3.5 Implementar `confirm_import(rows, materia_id, cohorte_id, cargado_por_id, tenant_id) → VersionPadron`: crea `VersionPadron` + `EntradaPadron` (emails cifrados, `usuario_id` resuelto), llama `activate_version`, genera audit `PADRON_CARGAR`
- [x] 3.6 Agregar test de triangulación: import con mezcla de alumnos con y sin cuenta de usuario; verificar que `usuario_id` se resuelve correctamente para los que tienen y queda null para los que no

## 4. Endpoints de importación

- [x] 4.1 Crear router `app/routers/padron.py` con prefijo `/api/padron`
- [x] 4.2 `POST /api/padron/preview` — recibe `UploadFile`, valida tamaño (default 5 MB → 413), llama service, retorna `PadronPreviewResponse`; guard `require_permission("padron:cargar")` + validación scope propio
- [x] 4.3 `POST /api/padron/confirm` — recibe `UploadFile` + `materia_id` + `cohorte_id`, ejecuta el confirm; guard ídem
- [x] 4.4 Registrar el router en `app/main.py`
- [x] 4.5 Escribir tests de integración: PROFESOR importa materia propia → 200, PROFESOR importa materia ajena → 403, sin permiso → 403, archivo sin columnas obligatorias → 422, archivo > 5 MB → 413

## 5. Vaciar padrón (scope-isolated)

- [x] 5.1 Implementar `PadronRepository.soft_delete_all_versions(materia_id, asignacion_id, tenant_id)`: marca `deleted_at` en todas las `VersionPadron` y sus `EntradaPadron` del scope dado
- [x] 5.2 Escribir tests primero: vaciado solo afecta el scope del actor, el scope de otro docente en la misma materia no se toca
- [x] 5.3 `DELETE /api/padron/{materia_id}` — guard `padron:cargar` + scope propio; llama service; retorna `204 No Content`; genera audit `PADRON_VACIAR`

## 6. Cliente Moodle WS

- [x] 6.1 Crear `app/integrations/moodle_ws.py` con dataclasses `MoodleUser`, `MoodleActivity`, `SyncResult` y clase `MoodleWSClient`
- [x] 6.2 Escribir tests primero (mock HTTP): sync exitosa mapea usuarios a `PadronImportRow`, error HTTP → `MoodleWSError`, schema inválido → `MoodleWSError`, tenant sin `moodle_url` → `MoodleNotConfiguredError`
- [x] 6.3 Implementar `MoodleWSClient.get_enrolled_users(course_id) → list[MoodleUser]`: llamada a `core_enrol_get_enrolled_users` de Moodle WS
- [x] 6.4 Implementar manejo de errores: todo status >= 400 o timeout → `MoodleWSError` con `retry_after=60`; loggear error en JSON estructurado; NO exponer el error crudo al cliente
- [x] 6.5 Agregar a `app/core/config.py` (Settings) campos opcionales: `moodle_url: str | None = None`, `moodle_token: str | None = None`

## 7. Endpoint de sync on-demand

- [x] 7.1 Escribir tests primero: sync con Moodle configurado → 200 + audit `PADRON_CARGAR`, Moodle no configurado → 422 `MOODLE_NOT_CONFIGURED`, Moodle WS falla → 502
- [x] 7.2 `POST /api/padron/moodle-sync` — body: `{materia_id, cohorte_id, course_id}`; guard `padron:cargar`; llama `MoodleWSClient.sync_padron(...)` → ejecuta pipeline confirm; retorna `PadronPreviewResponse` con origen `moodle_ws`

## 8. Scheduler de sync nocturna

- [x] 8.1 Crear tarea periódica en el worker async (`app/workers/padron_sync_worker.py`): itera tenants con `moodle_url` configurado y combinaciones con `course_id` asociado
- [x] 8.2 Lógica de skip silencioso: si tenant sin `moodle_url` → skip sin log; si `MoodleWSError` → log de error pero continuar con el siguiente tenant
- [x] 8.3 Registrar la tarea en el ciclo de vida del worker (sin APScheduler externo — misma infraestructura de worker async de C-01)
- [x] 8.4 Test de la lógica de skip: tenant sin Moodle configurado no genera llamadas HTTP al cliente

## 9. Cobertura y aislamiento final

- [x] 9.1 Test de aislamiento multi-tenant end-to-end: dos tenants importan padrón para el mismo `materia_id`; verificar que cada tenant solo ve su propia versión activa
- [x] 9.2 Test de audit trail: toda operación `confirm` y `vaciar` genera el `AuditLog` correcto con `filas_afectadas`; el `detalle` del log no contiene emails en claro
- [x] 9.3 Verificar cobertura ≥ 80% líneas del módulo padron y ≥ 90% de las reglas de negocio (versionado, cifrado, scope-isolated, resolución usuario_id)
