## ADDED Requirements

### Requirement: Guard require_permission fail-closed
El sistema SHALL proveer una dependency FastAPI `require_permission(codigo: str)` que, usada en un endpoint, verifique que el usuario autenticado posee el permiso indicado. Si no lo posee, SHALL lanzar `HTTPException 403`.

#### Scenario: Usuario con permiso accede al endpoint
- **WHEN** un endpoint declara `require_permission("comunicacion:enviar")`
- **AND** el usuario autenticado tiene ese permiso en su conjunto efectivo
- **THEN** la petición continúa normalmente

#### Scenario: Usuario sin permiso recibe 403
- **WHEN** un endpoint declara `require_permission("comunicacion:enviar")`
- **AND** el usuario autenticado NO tiene ese permiso
- **THEN** el sistema responde `HTTP 403 Forbidden`

#### Scenario: Endpoint sin require_permission no aplica autorización
- **WHEN** un endpoint no declara `require_permission`
- **THEN** no se verifica permiso adicional (la autorización queda a cargo de otra lógica o es un endpoint público)

### Requirement: require_permission resuelve permisos server-side
El sistema SHALL, al evaluar `require_permission`, resolver los permisos efectivos del usuario consultando la matriz `rol_permiso` en base de datos, filtrada por tenant, y NO usar claims del JWT más allá de la lista de roles.

#### Scenario: Cambio en matriz se refleja inmediatamente
- **WHEN** un administrador asigna un nuevo permiso a un rol
- **AND** un usuario con ese rol realiza una petición inmediatamente después
- **THEN** el usuario ya tiene acceso al nuevo permiso sin necesidad de re-login

### Requirement: require_permission retorna contexto de permiso
El sistema SHALL hacer que `require_permission` devuelva un objeto `PermissionContext` que incluya `has_permission: bool`, `is_propio: bool` y el conjunto de permisos efectivos del usuario.

#### Scenario: Endpoint accede a contexto de propiedad
- **WHEN** un endpoint declara `require_permission("calificaciones:importar")`
- **AND** el usuario tiene ese permiso con `is_propio = true`
- **THEN** el endpoint recibe `PermissionContext` con `is_propio = true`
- **AND** el service puede aplicar el filtro de datos propios
