# Auth Shell — Spec

> Layout, route guards, permissions, sidebar, topbar, and Axios interceptors.

---

## REQ-SHELL-01: ProtectedRoute checks isAuthenticated. If false -> redirect to /login

The ProtectedRoute component wraps routes that require authentication.

### Scenarios

**Scenario 1: Authenticated user accesses protected route**
GIVEN the user is authenticated (isAuthenticated = true)
WHEN the user navigates to any protected route (e.g., /dashboard, /alumnos)
THEN the ProtectedRoute renders the child component
AND the user sees the intended page content

**Scenario 2: Unauthenticated user accesses protected route**
GIVEN the user is not authenticated (isAuthenticated = false)
AND isLoading is false (initial session check completed)
WHEN the user navigates to any protected route
THEN the user is redirected to /login
AND the original URL is preserved as a query parameter (?redirect=/original-path)

**Scenario 3: Post-login redirect to original URL**
GIVEN the user was redirected from /alumnos to /login?redirect=/alumnos
WHEN the user completes login successfully
THEN the user is redirected to /alumnos instead of the default /

---

## REQ-SHELL-02: While isLoading (initial session check), show Spinner

During the initial auth check (on page load or tab open), a loading indicator is displayed.

### Scenarios

**Scenario 1: Initial load shows spinner**
GIVEN the user opens the application in a new tab
WHEN the AuthProvider is checking the session (calling GET /api/auth/me)
THEN a full-screen centered Spinner is displayed
AND the Spinner has aria-label="Cargando sesión"
AND no route content is rendered

**Scenario 2: Session check completes**
GIVEN the Spinner is displayed during initial load
WHEN GET /api/auth/me completes (success or failure)
THEN isLoading becomes false
AND the Spinner is replaced by either the protected layout (if authenticated) or the login page (if not)

---

## REQ-SHELL-03: PermissionGuard checks user.roles for required role. If not -> redirect to /

The PermissionGuard component restricts access to routes based on user roles.

### Scenarios

**Scenario 1: User has required role**
GIVEN the user is authenticated
AND the current route requires permission "alumnos:read"
AND the user has the role containing "alumnos:read"
WHEN the PermissionGuard renders
THEN the child component is rendered normally

**Scenario 2: User does NOT have required role**
GIVEN the user is authenticated
AND the current route requires permission "liquidaciones:read"
AND the user does NOT have any role with "liquidaciones:read"
WHEN the PermissionGuard renders
THEN the user is redirected to /
AND a toast "No tenés permiso para acceder a esta página" is shown

**Scenario 3: PermissionGuard requires multiple roles**
GIVEN a route requires ["alumnos:read", "materias:read"]
AND the user has only "alumnos:read"
WHEN the PermissionGuard renders
THEN the user is redirected to /
AND a toast is shown

**Scenario 4: PermissionGuard with any match (OR logic)**
GIVEN a route requires at least one of ["coordinador", "admin"]
AND the user has the "coordinador" role
WHEN the PermissionGuard renders
THEN the child component is rendered

---

## REQ-SHELL-04: Layout renders Sidebar (left) + main content (right) via Outlet

The main application layout has a fixed sidebar and a scrollable content area using react-router-dom's Outlet.

### Scenarios

**Scenario 1: Layout renders with sidebar and content**
GIVEN the user is authenticated
WHEN any authenticated route renders
THEN the Layout component is displayed
AND a Sidebar is visible on the left (or collapsed on mobile)
AND a main content area is visible on the right
AND the main content renders the matched child route via Outlet

**Scenario 2: Sidebar width is fixed on desktop**
GIVEN the Layout is rendered on a desktop viewport (>= 1024px)
WHEN the user views the page
THEN the Sidebar has a fixed width of 256px (w-64)
AND the main content fills the remaining horizontal space

---

## REQ-SHELL-05: Sidebar shows navigation links based on user roles

The sidebar dynamically renders navigation items based on the authenticated user's permissions.

### Scenarios

**Scenario 1: Admin sees all navigation links**
GIVEN the authenticated user has the "admin" role
WHEN the Sidebar renders
THEN links for all available modules are visible: Alumnos, Materias, Comisiones, Comunicación, Equipos, Liquidaciones
AND each link shows a lucide-react icon + label

**Scenario 2: Tutor sees limited navigation links**
GIVEN the authenticated user has only the "tutor" role
WHEN the Sidebar renders
THEN only permitted links are visible (e.g., Alumnos, Comunicación)
AND links to Liquidaciones are NOT visible

**Scenario 3: Active link is highlighted**
GIVEN the user navigates to /alumnos
WHEN the Sidebar renders
THEN the "Alumnos" link has an active visual state (different background color)
AND all other links have the default visual state

**Scenario 4: Sidebar link triggers navigation**
GIVEN the Sidebar is displayed
WHEN the user clicks a navigation link (e.g., "Materias")
THEN the browser navigates to /materias
AND the active state updates to highlight the Materias link

---

## REQ-SHELL-06: Topbar shows user email + logout button

The top bar provides user context and a logout action.

### Scenarios

**Scenario 1: Topbar renders user info**
GIVEN the user is authenticated
WHEN the Layout renders
THEN the Topbar is visible at the top of the content area (not in the sidebar)
AND the user's email is displayed
AND a logout button or icon is visible

**Scenario 2: Mobile menu toggle (optional)**
GIVEN the Layout is rendered on a mobile viewport (< 1024px)
WHEN the user views the page
THEN the Topbar shows a hamburger menu button (Menu icon from lucide-react)
AND clicking it toggles the Sidebar visibility

---

## REQ-SHELL-07: On logout click, POST /api/auth/logout -> clear session -> redirect to /login

Logout is an explicit action that invalidates the server-side session and clears local state.

### Scenarios

**Scenario 1: Successful logout**
GIVEN the user is authenticated
WHEN the user clicks the logout button
THEN a POST request is sent to /api/auth/logout
AND the AuthProvider clears the access_token
AND user is set to null
AND isAuthenticated is set to false
AND the user is redirected to /login

**Scenario 2: Logout API fails (network error)**
GIVEN the user is authenticated
WHEN the user clicks the logout button
AND POST /api/auth/logout fails (network error or 500)
THEN local session is still cleared (access_token removed, user set to null)
AND the user is redirected to /login
AND the server-side cookie will expire naturally

---

## REQ-SHELL-08: Root / redirects to first available feature based on roles

The root URL acts as a smart redirect to the first feature the user can access.

### Scenarios

**Scenario 1: Admin visits /**
GIVEN the user is authenticated with the "admin" role
WHEN the user navigates to /
THEN the user is redirected to /alumnos (first feature in priority order)

**Scenario 2: Tutor visits /**
GIVEN the user is authenticated with only the "tutor" role
WHEN the user navigates to /
THEN the user is redirected to the first feature permitted by their role

**Scenario 3: No features available (fallback)**
GIVEN the user is authenticated but has no roles granting access to any feature
WHEN the user navigates to /
THEN a fallback page "No tenés acceso a ningún módulo" is displayed
AND the user sees a logout button

---

## REQ-SHELL-09: Layout is responsive: sidebar collapses on mobile

The layout adapts to viewport size for mobile usability.

### Scenarios

**Scenario 1: Desktop layout**
GIVEN the viewport is >= 1024px
WHEN the Layout renders
THEN the Sidebar is permanently visible on the left
AND the main content is offset to the right

**Scenario 2: Mobile layout with collapsed sidebar**
GIVEN the viewport is < 1024px
WHEN the Layout renders
THEN the Sidebar is hidden by default
AND a hamburger menu icon is visible in the Topbar
AND clicking the menu icon slides the Sidebar in from the left
AND clicking outside the Sidebar or on a navigation link closes it

**Scenario 3: Sidebar overlay on mobile**
GIVEN the Sidebar is open on mobile
WHEN the user taps outside the Sidebar (on the overlay area)
THEN the Sidebar closes
AND the overlay is removed

---

## REQ-SHELL-10: Impersonation banner shown when is_impersonating=true (yellow warning)

When an admin is impersonating another user, a persistent warning banner is shown.

### Scenarios

**Scenario 1: Impersonation banner visible**
GIVEN the user is authenticated
AND the MeResponse has is_impersonating = true
WHEN the Layout renders
THEN a yellow/orange warning banner is displayed at the top of the page
AND the banner text is "Estás operando como {user.nombre} {user.apellido}"
AND a "Salir de impersonación" button is visible on the banner

**Scenario 2: Stop impersonation**
GIVEN the impersonation banner is visible
WHEN the user clicks "Salir de impersonación"
THEN a POST request is sent to /api/auth/impersonation/stop
AND the AuthProvider refetches the original admin session
AND the banner disappears

**Scenario 3: Non-impersonated user sees no banner**
GIVEN the user is authenticated
AND is_impersonating = false
WHEN the Layout renders
THEN no impersonation banner is visible
AND the layout renders normally

---

## REQ-SHELL-11: Axios interceptor auto-attaches Bearer token from AuthProvider

Every outgoing API request includes the access token when available.

### Scenarios

**Scenario 1: Authenticated request includes token**
GIVEN an access_token is stored in the AuthProvider
WHEN any Axios request is made to the API
THEN the request includes an Authorization header: "Bearer {access_token}"
AND the request includes withCredentials = true

**Scenario 2: Unauthenticated request has no token**
GIVEN no access_token is stored
WHEN any Axios request is made to the API
THEN no Authorization header is attached
AND the request is sent as-is

**Scenario 3: Token changes mid-session (refresh)**
GIVEN the access_token was refreshed
WHEN a new request is made after the refresh
THEN the Authorization header uses the NEW access_token
AND no Authorization header with the old token is sent

---

## REQ-SHELL-12: Axios interceptor on 401 response: try POST /api/auth/refresh, queue concurrent requests

When a 401 occurs, the interceptor attempts a transparent token refresh and replays any queued requests.

### Scenarios

**Scenario 1: Single 401 triggers refresh**
GIVEN the user is authenticated with an expired access_token
WHEN a single API request returns 401
THEN the interceptor intercepts the 401
AND sends POST /api/auth/refresh (cookie-based, no body)
AND if refresh succeeds (200 with new access_token):
  - the new token is stored in the AuthProvider
  - the original request is retried with the new token
  - the response is returned to the caller

**Scenario 2: Concurrent 401s during refresh (request queue)**
GIVEN an API request triggers a 401 and the refresh is in flight
WHEN 3 additional API requests also return 401 simultaneously
THEN the interceptor queues the 3 additional requests
AND only ONE POST /api/auth/refresh is sent
AND when the refresh completes:
  - all 4 queued requests are retried with the new token
  - each receives its respective response

**Scenario 3: Concurrent 401s with failed refresh**
GIVEN the refresh is in flight
WHEN multiple requests are queued
AND POST /api/auth/refresh returns 401 (refresh cookie also expired)
THEN all queued requests are rejected
AND the AuthProvider clears the session
AND the user is redirected to /login

**Scenario 4: Refresh endpoint returns 401**
GIVEN the refresh cookie has expired
WHEN POST /api/auth/refresh returns 401
THEN the interceptor does NOT retry the refresh
AND the interceptor rejects all queued requests with the 401
AND the AuthProvider clears access_token
AND the user is redirected to /login

---

## REQ-SHELL-13: If refresh fails, clear session and redirect to login

Failed token refresh means the session is irrecoverable — the user must log in again.

### Scenarios

**Scenario 1: Refresh fails (network error)**
GIVEN POST /api/auth/refresh fails with a network error
WHEN the interceptor receives the error
THEN the access_token is cleared from the AuthProvider
AND user is set to null
AND isAuthenticated is set to false
AND the user is redirected to /login
AND any queued requests are rejected

**Scenario 2: Refresh returns 500**
GIVEN POST /api/auth/refresh returns 500
WHEN the interceptor receives the error
THEN the access_token is cleared
AND the user is redirected to /login
AND a generic "Sesión expirada. Iniciá sesión de nuevo." message is shown

---

## REQ-SHELL-14: Axios instance has withCredentials=true for cookie support

The centralized Axios client includes credentials (HttpOnly refresh cookie) in every request.

### Scenarios

**Scenario 1: Axios instance configuration**
GIVEN the application initializes the Axios instance
WHEN the instance is created
THEN withCredentials is set to true
AND the baseURL is set from VITE_API_BASE_URL (or defaults to "" for Vite proxy)
AND the Content-Type header defaults to application/json

**Scenario 2: Cookie sent with every API request**
GIVEN the Axios instance has withCredentials = true
WHEN any request is made to the API
THEN HttpOnly cookies (including the refresh_token cookie) are included in the request
AND no JavaScript code can read the cookie value directly
