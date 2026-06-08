## Context

C-04 está completo: tenemos identidad (JWT), multi-tenancy (row-level) y RBAC (require_permission). El sistema puede saber quién hace qué, pero no lo registra. C-05 cierra ese gap: toda acción significativa debe quedar inmortalizada con actor, tenant y contexto. Adicionalmente, la funcionalidad de impersonación (ADMIN operando en nombre de otro usuario) necesita un token distinguible y una atribución correcta en el audit trail.

El backend ya tiene: `TenantMixin`, `SoftDeleteMixin`, base de repositorios async con scope tenant, guard `require_permission`, y tres migraciones previas (001 tenant/models, 002 rbac, 003 auth).

## Goals / Non-Goals

**Goals:**
- Tabla `audit_log` inmutable a nivel DB: no UPDATE, no DELETE, nunca.
- Helper `record_audit()` explícito, reutilizable desde la capa Service.
- Enum `AuditAction` con catálogo inicial de códigos de acción.
- Endpoints `POST/DELETE /api/auth/impersonate` con permiso `impersonacion:usar`.
- JWT de impersonación con claims `imp: true` y `act: <actor_uuid>`; resolución correcta en `get_current_user`.
- Toda acción bajo impersonación atribuida al actor real, no al impersonado.

**Non-Goals:**
- UI/dashboard de auditoría (C-19).
- Queries analíticas ni exportación del log (C-19).
- Rotación, retención o archivado de registros.
- Auditoría automática de todos los endpoints (solo acciones explícitamente marcadas).

## Decisions

### D-01: Append-only a nivel DB con trigger BEFORE UPDATE/DELETE

**Alternativas:**
- A) Solo restricción en la app (Repository sin métodos update/delete).
- B) PostgreSQL RULE (`ON UPDATE DO INSTEAD NOTHING`).
- C) **BEFORE trigger que lanza RAISE EXCEPTION** en UPDATE o DELETE.
- D) REVOKE de privilegios UPDATE/DELETE al rol de la app.

**Elección: C (trigger BEFORE)**. La opción A se puede bypassear con SQL directo o scripts de migración. La B silencia la operación sin error, enmascarando bugs. La D es válida pero no portable a entornos donde el usuario de la app tiene privilegios amplios. El trigger C es explícito, falla ruidosamente, está en la migración, y sobrevive a cualquier cambio del ORM o de la capa de acceso.

Implementación en migración 004:
```sql
CREATE OR REPLACE FUNCTION deny_audit_log_mutation()
RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'audit_log is immutable: % on row % is not allowed', TG_OP, OLD.id;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_log_immutable
BEFORE UPDATE OR DELETE ON audit_log
FOR EACH ROW EXECUTE FUNCTION deny_audit_log_mutation();
```

El modelo SQLAlchemy **no hereda `SoftDeleteMixin`**. No tiene `deleted_at`, `updated_at` ni ningún campo mutable post-inserción.

### D-02: Impersonación via claims JWT — sin estado adicional

**Alternativas:**
- A) Flag en DB/Redis: revocable inmediatamente pero requiere lookup en cada request.
- B) **Claims en JWT (`imp: true`, `act: <actor_uuid>`)**: stateless, consistente con el auth existente.

**Elección: B**. El token de impersonación es de corta duración (15 min, igual que el access token normal). Si hay que revocar antes, el ADMIN puede iniciar un nuevo `POST /api/auth/impersonate` o hacer logout del actor. La consistencia con el modelo stateless existente pesa más que la revocación inmediata, que es un caso excepcional.

Claims del JWT de impersonación:
```
sub      = target_user_id       # quién se impersona
act      = actor_user_id        # quién impersona (real)
imp      = true
tenant_id = tenant del actor    # siempre el tenant del actor
roles    = roles del target_user
type     = "access"
```

`get_current_user` expone una `ImpersonationContext` con `actor_id` y `impersonated_id`. El `actor_id` es el que va al campo `actor_id` del `AuditLog`.

### D-03: Helper explícito, no middleware automático

**Alternativas:**
- A) **Función `record_audit()` llamada explícitamente desde Services**.
- B) Middleware que intercepta requests y loguea automáticamente.

**Elección: A**. El código `accion` y `filas_afectadas` son de dominio: solo el Service sabe cuántos registros afectó o qué código de acción aplica. Un middleware solo puede loguear el endpoint y el status code, que es insuficiente para la semántica del negocio. La función explícita también hace los tests directos y simples.

`record_audit` firma:
```python
async def record_audit(
    session: AsyncSession,
    actor_id: UUID,
    tenant_id: UUID,
    accion: AuditAction,
    *,
    impersonado_id: UUID | None = None,
    materia_id: UUID | None = None,
    detalle: dict | None = None,
    filas_afectadas: int = 0,
    ip: str | None = None,
    user_agent: str | None = None,
) -> None: ...
```

### D-04: Estructura de archivos

```
backend/app/
├── core/
│   └── audit.py            # AuditAction enum + record_audit()
├── models/
│   └── audit_log.py        # AuditLog SQLAlchemy model
├── repositories/
│   └── audit_log_repository.py  # insert + query (sin update/delete)
├── services/
│   └── audit_service.py    # fina capa de servicio (opcional, puede ser thin wrapper)
├── api/v1/routers/
│   └── auth.py             # + POST/DELETE /impersonate
└── core/
    └── dependencies.py     # get_current_user + ImpersonationContext
```

## Risks / Trade-offs

| Riesgo | Mitigación |
|--------|------------|
| Developer olvida llamar `record_audit()` → acción no auditada | Code review; naming convention clara; tests de integración que verifican que el log tiene entradas post-acción |
| JWT de impersonación interceptado → actor malicioso opera como otro usuario | Vida corta (15 min); requiere `impersonacion:usar` (solo ADMIN); log de inicio/fin; HTTPS obligatorio |
| Trigger DB falla en entorno de test con DB efímera | El trigger se crea en la migración; los tests de migración ya validan aplicación y rollback |
| `act` claim en JWT aumenta tamaño del token | Un UUID extra (~36 bytes): impacto despreciable |

## Migration Plan

1. `backend/alembic/versions/004_audit_log.py` — crea tabla `audit_log` + función `deny_audit_log_mutation` + trigger `trg_audit_log_immutable`.
2. Rollback: `DROP TRIGGER`, `DROP FUNCTION`, `DROP TABLE audit_log`.
3. No hay datos existentes que migrar.
4. No hay cambios en tablas existentes (additive only).

## Open Questions

Ninguna pendiente para este change.
