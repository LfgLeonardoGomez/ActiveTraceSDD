## Context

C-09 se apoya en C-07 (Usuario + Asignacion) y habilita C-10 (Calificaciones). Su trabajo central es establecer la fuente de verdad de "quiénes son los alumnos" de cada materia × cohorte, mediante dos vías de ingesta: upload de archivo (xlsx/csv) y sincronización con Moodle Web Services.

**Constraint importante**: hay una discrepancia entre `05_reglas_de_negocio.md` RN-05 (que describe un upsert destructivo sin historial) y `04_modelo_de_datos.md` (que describe `VersionPadron` como entidad versionada que conserva historial). El CHANGES.md es explícito en que el modelo a implementar usa `VersionPadron` + activar/desactivar versiones. Se adopta el modelo de datos: **padrón versionado, la versión anterior no se borra, solo se desactiva**. Esta decisión da soporte a auditoría y a eventual rollback de padrón.

## Goals / Non-Goals

**Goals:**
- Modelos `VersionPadron` + `EntradaPadron` con restricción de una sola versión activa por `(tenant_id, materia_id, cohorte_id)`.
- Pipeline de import: parse → validate → preview → confirm → persist + audit.
- Cliente `moodle_ws.py` con sync on-demand y scheduler nocturno.
- Endpoint para vaciar padrón scope-isolated (RN-04).
- Toda `EntradaPadron.email` cifrada en reposo (AES-256).

**Non-Goals:**
- Importación de calificaciones (C-10).
- UI de importación (C-22).
- Configuración de la instancia Moodle por tenant (se asume variable de entorno por ahora).
- Deduplicación de alumnos entre versiones de padrón (C-10 usa la versión activa).

## Decisions

### D-01: Modelo versionado vs. upsert destructivo

**Decisión**: adoptar `VersionPadron` versionado (04_modelo_de_datos.md), no el upsert destructivo de RN-05.

**Alternativas consideradas**:
- Upsert destructivo (RN-05): más simple, menos storage, pero impide auditar "qué tenía el padrón antes del import" y rompe la FK de `EntradaPadron` en `Calificacion`.
- Versionado (adoptado): al activar una nueva versión se desactiva la anterior sin borrarla. El histórico permite auditoría y eventualmente correlacionar calificaciones de versiones distintas.

**Mecanismo**: `VersionPadron.activa` booleano; la restricción de una sola activa por `(tenant_id, materia_id, cohorte_id)` se aplica en el service (no DB constraint) para poder hacer el swap atómico dentro de una transacción.

---

### D-02: Pipeline de import en dos fases

**Decisión**: separar el import en dos requests: `POST /api/padron/preview` (parse + validate, retorna resultado pero no persiste) y `POST /api/padron/confirm` (persiste la versión nueva + desactiva la anterior).

**Alternativas consideradas**:
- Un solo request con persistencia: más simple, pero impide que el usuario valide antes de comprometerse con el cambio.
- Sesión temporal con ID de preview: requiere almacenamiento temporal (cache/DB). Se prefiere re-parse en confirm para no mantener estado entre requests.

**Formato de columnas esperado** (xlsx/csv):
```
nombre | apellidos | email | comision | regional
```
La primera fila es header (case-insensitive, ignorar espacios). Filas con email vacío se rechazan.

---

### D-03: EntradaPadron.email cifrado — búsqueda por email

**Decisión**: `EntradaPadron.email` se almacena cifrado (AES-256, consistente con Usuario.email). No se indexa directamente. Las búsquedas por email se realizan descifrado en memoria en el service, o bien comparando el hash determinístico del email (si se agrega columna `email_hash` en el futuro — fuera de scope aquí).

**Trade-off**: sin índice en `email` cifrado, el lookup O(n) en padrones grandes. Para el MVP con padrones de decenas/cientos de alumnos esto es aceptable. Se registra como deuda técnica.

---

### D-04: Moodle WS Client — diseño del módulo

**Decisión**: cliente dedicado en `integrations/moodle_ws.py` con interfaz:
- `get_enrolled_users(course_id) → list[MoodleUser]`
- `get_course_activities(course_id) → list[MoodleActivity]`
- `sync_padron(materia_id, cohorte_id, course_id, actor_id) → SyncResult`

El cliente es stateless; la configuración (URL base, token) viene de `Settings` (Pydantic v2) por tenant o global.

**Sync nocturna**: implementada como tarea periódica en el worker async (no APScheduler externo). Un registro `MoodleSyncJob` almacena `last_sync_at` y `status` por `(tenant_id, materia_id, cohorte_id)` para poder reportar el estado de la última sync. Scope reducido: solo persiste si el tenant tiene `moodle_url` configurado.

**Errores**: cualquier falla HTTP del WS de Moodle resulta en `502 MoodleWSError` con campo `retry_after`. No se propaga el error crudo.

---

### D-05: Permisos de padrón

**Permiso requerido**: `padron:cargar`. PROFESOR lo tiene sobre sus materias (scope `(propio)`); COORDINADOR lo tiene sobre todas las materias del tenant.

El guard existente `require_permission` + el patrón `is_propio` de C-04 aplica directamente: el service valida que el `materia_id` de la request sea una materia asignada al usuario antes de proceder.

## Risks / Trade-offs

- **[Risk] El alumno no tiene cuenta de usuario**: `EntradaPadron.usuario_id` es nullable. C-10 deberá manejar el caso de entradas sin `usuario_id` al asociar calificaciones. → Mitigation: documentado en spec, C-10 lo hace explícito en su diseño.

- **[Risk] Moodle WS no disponible para todos los tenants**: el fallback manual (upload de archivo) ya está contemplado como path primario. → Mitigation: la integración Moodle es optional; si `moodle_url` no está configurado, el endpoint de sync devuelve `422 MoodleNotConfigured`.

- **[Risk] Archivos grandes (padrones con miles de alumnos)**: el parse se hace en memoria con `openpyxl` / `csv.DictReader`. → Mitigation: límite de tamaño de archivo (configurable, default 5 MB) en el endpoint. Si se supera → `413`.

- **[Risk] Inconsistencia entre RN-05 y modelo versionado**: si en el futuro se decide revertir a upsert destructivo, la migración requiere eliminar versiones inactivas y reestructurar la FK de Calificacion. → Mitigation: decisión documentada en D-01; cualquier cambio requiere nuevo change.

## Migration Plan

1. Aplicar migración `006_padron.py` (Alembic): crea `version_padron`, `entrada_padron`.
2. No hay datos pre-existentes de padrón; la migración no requiere seed ni transformación de datos.
3. Rollback: `alembic downgrade -1`. Tablas vacías, sin riesgo.

## Open Questions

- **OQ-C09-01**: ¿El campo `course_id` de Moodle se almacena en `Materia` o en `Asignacion`? Para sync nocturna es necesario saber qué curso de Moodle corresponde a qué materia × cohorte. Por ahora se pasa como parámetro del request on-demand; la sync nocturna queda deshabilitada hasta cerrar esta pregunta.
- **OQ-C09-02**: ¿Se necesita una columna `legajo` en `EntradaPadron`? El modelo de datos no lo incluye, pero algunos tenants pueden necesitarlo para correlacionar con registros históricos. Fuera de scope MVP — agregar como campo nullable en C-09 si el usuario lo confirma.
