# Avisos Acknowledgment Specification

## Purpose
Segmented visibility and read confirmation for all authenticated roles.

## Requirements

### Requirement: List Visible Avisos
The system MUST provide GET /api/avisos/mis-avisos for any authenticated user with `avisos:confirmar`. The list MUST contain only avisos where:
- activo = true
- deleted_at is null
- inicio_en <= now <= fin_en (RN-18)
- audience matches the user's role and context (RN-20):
  - Global: visible to all
  - PorRol: visible if rol_destino matches user's role (or rol_destino is null)
  - PorMateria: visible if user has assignment to materia_id
  - PorCohorte: visible if user has assignment to cohorte_id
The response MUST include a flag `acknowledged` per aviso.

#### Scenario: Global aviso visible
- GIVEN a Global aviso with active=true and inicio_en <= now <= fin_en
- WHEN GET /api/avisos/mis-avisos
- THEN the aviso is returned with acknowledged=false

#### Scenario: Aviso outside window is hidden
- GIVEN an aviso with fin_en < now
- WHEN GET /api/avisos/mis-avisos
- THEN the aviso is NOT returned

#### Scenario: PorRol aviso matches
- GIVEN a PorRol aviso with rol_destino=ALUMNO
- WHEN an ALUMNO requests mis-avisos
- THEN the aviso is returned

#### Scenario: PorRol aviso does not match
- GIVEN a PorRol aviso with rol_destino=PROFESOR
- WHEN an ALUMNO requests mis-avisos
- THEN the aviso is NOT returned

#### Scenario: Acknowledged aviso omitted
- GIVEN an aviso the user has already acknowledged
- WHEN GET /api/avisos/mis-avisos
- THEN the aviso is NOT returned (RN-19)

### Requirement: Acknowledge Aviso
The system MUST provide POST /api/avisos/{id}/confirmar for any authenticated user with `avisos:confirmar`. The system MUST create an AcknowledgmentAviso record with confirmado_at = now. The system MUST verify the aviso belongs to the user's tenant, is active, not deleted, and currently visible (RN-18). If aviso.requiere_ack is false, the system MUST still register the acknowledgment for view tracking. The system MUST return 409 if the user has already acknowledged.

#### Scenario: First acknowledgment
- GIVEN a visible aviso requiring ack
- WHEN POST /api/avisos/{id}/confirmar
- THEN an AcknowledgmentAviso is created
- AND the aviso no longer appears in mis-avisos

#### Scenario: Acknowledge optional aviso
- GIVEN a visible aviso with requiere_ack=false
- WHEN POST /api/avisos/{id}/confirmar
- THEN an AcknowledgmentAviso is created
- AND the aviso no longer appears in mis-avisos

#### Scenario: Duplicate acknowledgment
- GIVEN a user already acknowledged an aviso
- WHEN POST /api/avisos/{id}/confirmar
- THEN the system returns 409

### Requirement: Audit for Acknowledgment
The system MUST record an audit event with code AVISO_CONFIRMAR when a user successfully acknowledges an aviso.

#### Scenario: Audit on confirm
- GIVEN a user confirms an aviso
- THEN an AuditLog with accion=AVISO_CONFIRMAR is created
