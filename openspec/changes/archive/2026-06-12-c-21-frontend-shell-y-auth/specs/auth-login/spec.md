# Auth Login — Spec

## REQ-LOGIN-01: LoginForm renders email + password fields with Zod validation

LoginForm displays a form with two fields — email and password — validated client-side before submission.

### Scenarios

**Scenario 1: LoginForm renders both fields**
GIVEN the user navigates to /login
WHEN the LoginForm renders
THEN an email input field is visible
AND a password input field is visible
AND a submit button labeled "Iniciar sesión" is visible

**Scenario 2: Empty fields show validation errors**
GIVEN the LoginForm is displayed
WHEN the user clicks submit without filling any field
THEN an error "Email inválido" appears for the email field
AND an error "La contraseña debe tener al menos 8 caracteres" appears for the password field
AND the form is not submitted

**Scenario 3: Invalid email shows field-level error**
GIVEN the LoginForm is displayed
WHEN the user types "not-an-email" in the email field and submits
THEN the error "Email inválido" appears below the email input
AND no request is sent to the API

**Scenario 4: Short password shows field-level error**
GIVEN the LoginForm is displayed
WHEN the user types "abc" in the password field and submits
THEN the error "La contraseña debe tener al menos 8 caracteres" appears below the password input
AND no request is sent to the API

---

## REQ-LOGIN-02: On submit, POST /api/auth/login. If 2FA not enabled -> set session, redirect to /

Successful login without 2FA stores the session and navigates to the application root.

### Scenarios

**Scenario 1: Successful login without 2FA**
GIVEN the user has entered valid credentials
AND 2FA is not enabled for the account
WHEN the user clicks submit
THEN a POST request is sent to /api/auth/login with email and password
AND the response contains an access_token
AND the AuthProvider stores the access_token in a module variable
AND GET /api/auth/me is called to populate user context
AND the user is redirected to /

**Scenario 2: Network error shows generic message**
GIVEN the user has entered valid credentials
WHEN the user clicks submit
AND the network request fails (no response)
THEN an error message "Error de conexión. Intentá de nuevo." is displayed

---

## REQ-LOGIN-03: If 2FA enabled -> store pre_auth_token, redirect to /2fa

When 2FA is enabled, the login response contains a temporary token that authorizes the second step.

### Scenarios

**Scenario 1: Login with 2FA enabled**
GIVEN the user has entered valid credentials
AND 2FA is enabled for the account
WHEN the user clicks submit
THEN a POST request is sent to /api/auth/login with email and password
AND the response is 200 with a pre_auth_token field
AND the AuthProvider stores the pre_auth_token in memory
AND the user is redirected to /2fa

**Scenario 2: Direct navigation to /2fa without pre-auth**
GIVEN the user is not authenticated
WHEN the user navigates directly to /2fa
THEN the TwoFactorPage redirects to /login
AND no pre_auth_token is stored

---

## REQ-LOGIN-04: On 401 -> show "Credenciales inválidas" error message

Invalid credentials return a clear, user-friendly error.

### Scenarios

**Scenario 1: Wrong email shows error**
GIVEN the LoginForm is displayed
WHEN the user submits an email that does not exist in the system
AND any password
THEN a POST to /api/auth/login returns 401
AND the form displays "Credenciales inválidas" as a general error (not field-level)
AND the password field is cleared
AND the email field retains its value

**Scenario 2: Wrong password shows error**
GIVEN the LoginForm is displayed
WHEN the user submits a valid email with an incorrect password
THEN a POST to /api/auth/login returns 401
AND the form displays "Credenciales inválidas" as a general error
AND the password field is cleared

---

## REQ-LOGIN-05: On 429 (rate limit) -> disable submit, show countdown from Retry-After header

Rate limiting prevents brute-force attacks; the UI communicates the wait time clearly.

### Scenarios

**Scenario 1: Rate limited with Retry-After header**
GIVEN the user has submitted the login form 5 times within 60 seconds
WHEN the user submits again
THEN a POST to /api/auth/login returns 429
AND the submit button is disabled
AND a countdown message "Demasiados intentos. Esperá {seconds} segundos." is shown
AND the countdown decrements every second based on the Retry-After header value
AND when the countdown reaches 0, the submit button is re-enabled
AND the error message is removed

**Scenario 2: Rate limited without Retry-After header**
GIVEN the user has submitted the login form 5 times within 60 seconds
WHEN the user submits again
THEN a POST to /api/auth/login returns 429 without a Retry-After header
AND the submit button is disabled for 60 seconds (default)
AND a countdown message is displayed

**Scenario 3: Reload during countdown**
GIVEN the user is rate-limited and the countdown is active
WHEN the user reloads the page
THEN the rate-limit state is lost (in-memory only)
AND the user can attempt login again
AND the backend enforces the same rate limit server-side

---

## REQ-LOGIN-06: TwoFactorForm renders 6-digit TOTP input with Zod validation

The 2FA verification form accepts a single numeric code.

### Scenarios

**Scenario 1: TwoFactorForm renders correctly**
GIVEN the user is redirected to /2fa
AND a pre_auth_token is stored in the AuthProvider
WHEN the TwoFactorForm renders
THEN a single input field labeled "Código de verificación" is visible
AND the input accepts exactly 6 digits
AND a submit button labeled "Verificar" is visible

**Scenario 2: Non-numeric input is rejected**
GIVEN the TwoFactorForm is displayed
WHEN the user types letters or special characters
THEN the input value does not change (non-numeric characters are blocked)
OR a Zod validation error "El código debe ser numérico de 6 dígitos" is shown

**Scenario 3: Incomplete code fails validation**
GIVEN the TwoFactorForm is displayed
WHEN the user types only 4 digits and submits
THEN a Zod error "El código debe tener 6 dígitos" is shown
AND no request is sent to the API

---

## REQ-LOGIN-07: On 2FA submit, POST /api/auth/2fa/verify with pre_auth_token + code

The second step exchanges the pre_auth_token + TOTP for a real session.

### Scenarios

**Scenario 1: Valid 2FA submission**
GIVEN the TwoFactorForm is displayed
AND a pre_auth_token is stored
WHEN the user enters a valid 6-digit code and submits
THEN a POST request is sent to /api/auth/2fa/verify
WITH body containing pre_auth_token and code
AND the submit button shows a loading state

**Scenario 2: Loading state during verification**
GIVEN the TwoFactorForm is displayed
WHEN the user submits a valid code
AND the API request is in flight
THEN the submit button shows a Spinner
AND the submit button is disabled
AND the input fields are disabled

---

## REQ-LOGIN-08: On 2FA success -> set session, redirect to /

Successful 2FA completes the authentication flow.

### Scenarios

**Scenario 1: Successful 2FA verification**
GIVEN the user submitted a valid TOTP code
WHEN the POST to /api/auth/2fa/verify returns 200 with an access_token
THEN the AuthProvider stores the access_token in a module variable
AND GET /api/auth/me is called to populate user context
AND the pre_auth_token is cleared from memory
AND the user is redirected to /

---

## REQ-LOGIN-09: On 401 from 2FA (expired pre_auth_token) -> redirect to /login with "Sesión expirada" message

The pre_auth_token has a 5-minute expiry. If it expires before the user completes 2FA, they must start over.

### Scenarios

**Scenario 1: Expired pre_auth_token**
GIVEN the user has a stored pre_auth_token
WHEN the user submits a TOTP code
AND POST /api/auth/2fa/verify returns 401
THEN the AuthProvider clears the pre_auth_token
AND the user is redirected to /login
AND a message "Sesión expirada. Iniciá sesión de nuevo." is displayed

**Scenario 2: Invalid TOTP code**
GIVEN the user has a valid pre_auth_token
WHEN the user submits an incorrect TOTP code
AND POST /api/auth/2fa/verify returns 400
THEN an error "Código inválido" is shown on the TwoFactorForm
AND the code input is cleared
AND the pre_auth_token is retained (user can retry)

---

## REQ-LOGIN-10: On successful login, call GET /api/auth/me to populate user context

After authentication, the user profile is fetched to populate the AuthProvider context.

### Scenarios

**Scenario 1: /api/auth/me succeeds after login**
GIVEN the login (or 2FA) flow completed successfully
WHEN the AuthProvider calls GET /api/auth/me
THEN the response populates user in context
AND isAuthenticated is set to true
AND isLoading is set to false

**Scenario 2: /api/auth/me fails after login (unexpected)**
GIVEN the login (or 2FA) flow completed successfully
WHEN the AuthProvider calls GET /api/auth/me
AND the request fails (network error or 500)
THEN isLoading is set to false
AND isAuthenticated remains false
AND the user is redirected to /login with error "Error al cargar sesión"

**Scenario 3: TanStack Query caches /api/auth/me**
GIVEN the user is authenticated
WHEN the AuthProvider mounts
THEN GET /api/auth/me is fetched via TanStack Query
AND subsequent remounts use cached data until staleTime expires

---

## REQ-LOGIN-11: AuthProvider stores access_token in module variable (NOT localStorage)

The token is stored in a JavaScript module closure variable, invisible to XSS attacks that read from localStorage or sessionStorage.

### Scenarios

**Scenario 1: Module variable storage**
GIVEN the AuthProvider is initialized
WHEN a login succeeds and returns an access_token
THEN the token is stored in a module-level variable (outside React state)
AND the token is NOT stored in localStorage, sessionStorage, or any cookie accessible to JS
AND the same variable is used across all browser tabs (single-page scoped)

**Scenario 2: No token persistence across tabs**
GIVEN the user is authenticated in tab A
WHEN the user opens tab B
THEN tab B has no access_token
AND tab B shows a Spinner while checking session
AND tab B redirects to /login because no session cookie exists (auth is per-tab)

---

## REQ-LOGIN-12: AuthProvider exposes: user, isAuthenticated, isLoading, login(), verify2FA(), logout()

The AuthContext provides a stable interface for all consumer components.

### Scenarios

**Scenario 1: Context shape before authentication**
GIVEN no user is authenticated
WHEN any component consumes AuthContext
THEN user is null
AND isAuthenticated is false
AND isLoading is true (initial check) or false (after check completed)
AND login is a function
AND verify2FA is a function
AND logout is a function

**Scenario 2: Context shape after authentication**
GIVEN the user is authenticated
WHEN any component consumes AuthContext
THEN user contains the MeResponse (id, email, nombre, apellido, roles, tenant_id, is_impersonating)
AND isAuthenticated is true
AND isLoading is false

**Scenario 3: calling login() with valid credentials**
GIVEN AuthContext is available
WHEN a component calls login({ email, password })
THEN the internal login function executes the full flow (REQ-LOGIN-02/03/10)

**Scenario 4: calling verify2FA() with code**
GIVEN AuthContext is available
AND a pre_auth_token is stored
WHEN a component calls verify2FA({ code })
THEN the internal verify function executes the full flow (REQ-LOGIN-07/08)

**Scenario 5: calling logout()**
GIVEN AuthContext is available
AND the user is authenticated
WHEN a component calls logout()
THEN POST /api/auth/logout is sent
AND the access_token is cleared
AND user is set to null
AND isAuthenticated is set to false
AND the user is redirected to /login
