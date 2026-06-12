# Perfil Edición Specification

## Purpose
Self-service profile editing for authenticated users. The endpoint resolves the target user exclusively from the JWT session, enforces read-only CUIL at schema level, and transparently encrypts/decrypts PII fields.

## Requirements

### Requirement: Self-service profile edit
The authenticated user MUST edit their own editable fields via `PATCH /api/v1/perfil`. The system SHALL resolve the target user exclusively from the JWT session and enforce a self-service guard at the service level.

#### Scenario: Edit own profile successfully
- GIVEN an authenticated user with permission `perfil:editar`
- WHEN `PATCH /api/v1/perfil` with `{nombre, apellidos, banco, regional, cbu, alias_cbu, legajo_profesional, facturador}`
- THEN 200 with updated user, PII encrypted at rest, audit `PERFIL_EDITAR` logged

#### Scenario: Attempt to edit another user
- GIVEN an authenticated user
- WHEN any payload or URL parameter attempts to target a different user identity
- THEN 403 forbidden (self-service guard enforces `current_user.id == target_user.id`)

#### Scenario: Soft-deleted user cannot edit
- GIVEN an authenticated user whose account is soft-deleted
- WHEN `PATCH /api/v1/perfil` is requested
- THEN 404 not found

### Requirement: CUIL read-only enforcement
The system MUST NOT allow mutation of `cuil`. The field SHALL be absent from the update DTO; the schema uses `extra='forbid'` so any `cuil` key in the payload is rejected.

#### Scenario: CUIL in payload rejected
- GIVEN an authenticated user
- WHEN `PATCH /api/v1/perfil` includes `{"cuil": "20-12345678-9"}`
- THEN 422 unprocessable entity (extra field forbidden by schema)

### Requirement: PII encryption on profile edit
Editable PII fields (`email`, `dni`, `cbu`, `alias_cbu`) MUST be encrypted with AES-256-GCM before storage and decrypted only in the response to the owning user.

#### Scenario: PII encrypted after edit
- GIVEN an authenticated user updates `cbu` and `email`
- WHEN the request is processed
- THEN the database stores encrypted values; the response returns decrypted plaintext only to the owner

## Permissions
- `perfil:editar` — granted to all authenticated users (self-service)

## Audit Codes
- `PERFIL_EDITAR` — logged on every successful profile edit
