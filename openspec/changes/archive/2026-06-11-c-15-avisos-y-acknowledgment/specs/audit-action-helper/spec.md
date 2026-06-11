# Delta for Audit Action Helper

## ADDED Requirements

### Requirement: Enum values for aviso actions
The system MUST extend `AuditAction` in `backend/app/core/audit.py` with the following codes: `AVISO_CREAR`, `AVISO_ACTUALIZAR`, `AVISO_ELIMINAR`, `AVISO_CONFIRMAR`.

#### Scenario: Create aviso triggers audit
- GIVEN a Service creates an aviso
- WHEN it invokes `record_audit(..., accion=AuditAction.AVISO_CREAR, ...)`
- THEN the stored `accion` is `"AVISO_CREAR"`

#### Scenario: Update aviso triggers audit
- GIVEN a Service updates an aviso
- WHEN it invokes `record_audit(..., accion=AuditAction.AVISO_ACTUALIZAR, ...)`
- THEN the stored `accion` is `"AVISO_ACTUALIZAR"`

#### Scenario: Delete aviso triggers audit
- GIVEN a Service soft-deletes an aviso
- WHEN it invokes `record_audit(..., accion=AuditAction.AVISO_ELIMINAR, ...)`
- THEN the stored `accion` is `"AVISO_ELIMINAR"`

#### Scenario: Acknowledge aviso triggers audit
- GIVEN a Service confirms an aviso
- WHEN it invokes `record_audit(..., accion=AuditAction.AVISO_CONFIRMAR, ...)`
- THEN the stored `accion` is `"AVISO_CONFIRMAR"`
