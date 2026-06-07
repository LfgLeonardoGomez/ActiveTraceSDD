## ADDED Requirements

### Requirement: Rate limiting en login
El sistema SHALL limitar los intentos de login a 5 por ventana de 60 segundos, claveados por combinación de IP + email.

#### Scenario: Login dentro del límite
- **WHEN** el usuario realiza 5 intentos de login fallidos o exitosos en menos de 60 segundos desde la misma IP y para el mismo email
- **THEN** el sistema procesa todas las peticiones normalmente

#### Scenario: Login excede el límite
- **WHEN** el usuario realiza un 6to intento de login dentro de la misma ventana de 60 segundos (misma IP + email)
- **THEN** el sistema responde con 429 Too Many Requests
- **AND** no ejecuta verificación de password ni emite tokens
- **AND** incluye header `Retry-After` con los segundos restantes hasta fin de ventana

#### Scenario: Ventana de rate limit se renueva
- **WHEN** pasan 60 segundos desde el primer intento del bucket
- **THEN** el contador se resetea a 0
- **AND** nuevos intentos son permitidos nuevamente hasta 5

### Requirement: Rate limiting por IP + email independiente
El rate limiting SHALL aplicarse por combinación IP + email, no por IP sola ni por email sola, para evitar bloqueo masivo de usuarios legítimos detrás de NAT ni bloqueo de un usuario por actividad de otro.

#### Scenario: Dos emails distintos desde misma IP
- **WHEN** se realizan 5 intentos con `userA@example.com` y 5 intentos con `userB@example.com` desde la misma IP dentro de 60 segundos
- **THEN** ambos flujos son permitidos (cada uno en su propio bucket)
- **AND** ninguno recibe 429 por el otro

#### Scenario: Dos IPs distintas para mismo email
- **WHEN** se realizan 5 intentos con `userA@example.com` desde IP1 y 5 intentos desde IP2
- **THEN** ambos flujos son permitidos (cada uno en su propio bucket)
- **AND** ninguno recibe 429 por el otro

### Requirement: Rate limiting en endpoints de autenticación sensibles
El sistema SHALL aplicar rate limiting en todos los endpoints de autenticación que puedan ser vectores de fuerza bruta o abuso.

#### Scenario: Rate limit en forgot password
- **WHEN** se realizan más de 5 solicitudes de `POST /api/auth/forgot` para la misma combinación IP + email en 60 segundos
- **THEN** el sistema responde con 429 Too Many Requests
- **AND** no genera token de recuperación

#### Scenario: Rate limit en 2FA verify
- **WHEN** se realizan más de 5 intentos de `POST /api/auth/2fa/verify` con el mismo `pre_auth_token` en 60 segundos
- **THEN** el sistema responde con 429 Too Many Requests
- **AND** invalida el `pre_auth_token`

### Requirement: Comportamiento seguro bajo rate limit
El sistema SHALL mantener comportamiento idéntico (tiempo de respuesta, código de status cuando aplica) independientemente de si el email existe o no, para evitar enumeración de usuarios.

#### Scenario: Respuesta idéntica para email existente e inexistente bajo rate limit
- **WHEN** un atacante envía múltiples requests a `POST /api/auth/forgot` con emails arbitrarios
- **THEN** las respuestas 202 (email existente) y 202 (email inexistente) tienen el mismo tiempo de respuesta (± delay constante)
- **AND** no se expone si el email existe en la base de datos
