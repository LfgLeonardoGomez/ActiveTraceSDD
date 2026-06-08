### Requirement: Endpoint de inicio de sesión de impersonación
El sistema SHALL exponer `POST /api/auth/impersonate` que acepta `{ "target_user_id": UUID }` y requiere el permiso `impersonacion:usar`. Al usarlo, emite un access token con claims de impersonación para el usuario target dentro del mismo tenant.

#### Scenario: Inicio de impersonación exitoso
- **WHEN** un usuario con permiso `impersonacion:usar` envía `POST /api/auth/impersonate` con `target_user_id` de un usuario activo del mismo tenant
- **THEN** el sistema responde con 200 y un access token con claims: `sub = target_user_id`, `act = actor_user_id`, `imp = true`, `tenant_id = tenant del actor`, `roles = roles del target`, `type = "access"`, `exp = now + 15 min`
- **AND** se registra `IMPERSONACION_INICIAR` en el `AuditLog` con `actor_id = actor`, `impersonado_id = target`, `tenant_id` del actor

#### Scenario: Impersonación sin permiso rechazada
- **WHEN** un usuario sin permiso `impersonacion:usar` intenta `POST /api/auth/impersonate`
- **THEN** el sistema responde con 403 Forbidden
- **AND** no emite ningún token ni registra auditoría

#### Scenario: Impersonación de usuario de otro tenant rechazada
- **WHEN** el actor intenta impersonar a un usuario cuyo `tenant_id` difiere del actor
- **THEN** el sistema responde con 404 (el target no existe en el tenant del actor)
- **AND** no emite token ni registra auditoría

#### Scenario: Impersonación de usuario inactivo rechazada
- **WHEN** el actor intenta impersonar a un usuario con `estado = Inactivo`
- **THEN** el sistema responde con 400 Bad Request con detalle indicando que el usuario target está inactivo

### Requirement: Endpoint de fin de sesión de impersonación
El sistema SHALL exponer `DELETE /api/auth/impersonate` que requiere un access token de impersonación activo (`imp = true`). Al usarlo, registra el fin de la impersonación en el audit log.

#### Scenario: Fin de impersonación exitoso
- **WHEN** un actor con token de impersonación activo envía `DELETE /api/auth/impersonate`
- **THEN** el sistema responde con 204 No Content
- **AND** registra `IMPERSONACION_FINALIZAR` en `AuditLog` con `actor_id = act claim`, `impersonado_id = sub claim`, `tenant_id`
- **AND** el token de impersonación expira naturalmente (no hay lista de revocación, duración 15 min)

#### Scenario: DELETE sin token de impersonación activo
- **WHEN** un usuario normal (sin `imp = true`) llama `DELETE /api/auth/impersonate`
- **THEN** el sistema responde con 400 Bad Request indicando que no hay sesión de impersonación activa

### Requirement: Resolución de identidad real bajo impersonación
El sistema SHALL, cuando `get_current_user` procesa un token con `imp = true`, exponer un `ImpersonationContext` que indica el `actor_id` (quien impersona) y el `impersonated_id` (a quién se impersona). El `actor_id` es el sujeto REAL para fines de auditoría; `impersonated_id` es el contexto bajo el que opera.

#### Scenario: ImpersonationContext disponible en endpoint protegido
- **WHEN** un endpoint recibe un token de impersonación válido
- **THEN** `get_current_user` retorna un objeto con `user_id = impersonated_id`, `actor_id = act claim`, `is_impersonating = True`
- **AND** los routers pueden acceder a `actor_id` para pasarlo a `record_audit`

#### Scenario: Token normal no tiene ImpersonationContext activo
- **WHEN** un endpoint recibe un token normal (sin `imp`)
- **THEN** `get_current_user` retorna `is_impersonating = False` y `actor_id = user_id`

### Requirement: Atribución de acciones bajo impersonación al actor real
El sistema SHALL, para toda llamada a `record_audit` durante una sesión de impersonación, usar el `actor_id` real (del claim `act`) como `actor_id` del `AuditLog`, y el `impersonated_id` como `impersonado_id`. Nunca se atribuye la acción al usuario impersonado.

#### Scenario: Acción auditada bajo impersonación atribuida al actor real
- **WHEN** el actor A impersona al usuario B y B realiza una acción que genera un `AuditLog`
- **THEN** el registro tiene `actor_id = A`, `impersonado_id = B`
- **AND** NO tiene `actor_id = B` ni `impersonado_id = NULL`
