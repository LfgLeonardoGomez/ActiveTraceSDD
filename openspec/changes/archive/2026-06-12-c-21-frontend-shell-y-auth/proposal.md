# Proposal: C-21 frontend-shell-y-auth

## Intent
Create the Single Page Application (SPA) shell for activia-trace with authentication, authorization guards, and shared UI infrastructure. This is the foundational frontend change that enables all future frontend features (C-22, C-23, C-24).

## Scope
1. Project scaffolding: Vite 6 + React 18 + TypeScript + Tailwind CSS v4 with @tailwindcss/vite plugin
2. Shared UI component library: Button, Input, Card, Label, Spinner using CVA (class-variance-authority) pattern
3. Auth module: Login, 2FA verification, Forgot Password, Reset Password pages
4. Axios API client: centralized instance with JWT request interceptor and transparent refresh token rotation
5. AuthProvider React Context: manages access token (in-memory), user session, authentication state
6. Route guards: ProtectedRoute (redirects to /login if unauthenticated), PermissionGuard (checks roles)
7. App Layout: responsive shell with Sidebar navigation, Topbar with user info/logout, main content area via Outlet
8. Landing page: root `/` redirect based on user roles

## Out of Scope
- Feature-specific pages (alumnos, materias, calificaciones, equipos, etc.) — belong to C-22/23/24
- CRUD tables, data grids, or form-heavy pages
- Real data visualization or reporting components
- E2E tests (unit tests for auth flow and guards included)

## Tech Stack
| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| Framework | React + TypeScript | 18.3.x | NOT React 19 |
| Bundler | Vite | 6.x | with @vitejs/plugin-react |
| Routing | react-router-dom | 6.28.x | NOT v7 (framework mode) |
| Server State | @tanstack/react-query | 5.62.x | All data fetching |
| Forms | react-hook-form + zod | 7.54.x / 3.24.x | Typed validation |
| HTTP | axios | 1.7.x | Centralized client |
| CSS | Tailwind CSS | 4.x | @tailwindcss/vite plugin |
| Utilities | clsx + tailwind-merge | latest | cn() helper |
| Icons | lucide-react | latest | Lightweight icons |
| Testing | vitest + @testing-library/react | latest | Component/unit tests |

## Architecture

### Auth Flow
1. User enters credentials -> POST /api/auth/login
2. If no 2FA: receive access_token + HttpOnly refresh cookie
3. If 2FA enabled: receive pre_auth_token -> prompt for TOTP -> POST /api/auth/2fa/verify -> access_token + cookie
4. Access token stored in module variable (NOT localStorage — XSS protection)
5. Refresh token in HttpOnly cookie with path=/api/auth/refresh (invisible to JS)
6. Axios response interceptor catches 401 -> tries POST /api/auth/refresh -> retries original request
7. If refresh fails -> clear token -> redirect to /login

### State Management
- AuthProvider React Context holds: user (MeResponse), accessToken, isAuthenticated, isLoading
- TanStack Query for GET /api/auth/me (auto-fetches after login, invalidated on logout)
- usePermissions hook derives UI capabilities from user.roles

### Development Proxy
- Vite dev server proxies /api/* to backend http://localhost:8000
- Avoids CORS issues in development
- Cookies flow through Vite proxy correctly

## Directory Structure
```
frontend/
├── index.html
├── package.json
├── tsconfig.json / tsconfig.app.json / tsconfig.node.json
├── vite.config.ts
├── .env (VITE_API_BASE_URL)
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css (@import "tailwindcss" + @theme)
│   ├── lib/utils.ts (cn helper)
│   ├── features/
│   │   └── auth/
│   │       ├── components/ (LoginForm, TwoFactorForm, ForgotPasswordForm, ResetPasswordForm)
│   │       ├── hooks/ (useLogin, useMe, useLogout, useForgotPassword, useResetPassword)
│   │       ├── services/auth.api.ts
│   │       ├── types/auth.types.ts
│   │       └── pages/ (LoginPage, TwoFactorPage, ForgotPasswordPage, ResetPasswordPage)
│   └── shared/
│       ├── services/ (api.ts, AuthContext.tsx)
│       ├── components/
│       │   ├── ui/ (Button, Input, Card, Label, Spinner)
│       │   ├── Layout.tsx, Sidebar.tsx, Topbar.tsx
│       │   └── guards/ (ProtectedRoute, PermissionGuard)
│       └── hooks/ (usePermissions.ts)
```

## Dependencies
- C-04 (rbac-permisos-finos): COMPLETED [x] — provides roles via GET /api/auth/me
- C-03 (auth-jwt-2fa): COMPLETED [x] — all auth endpoints available

## Risks & Mitigations
| Risk | Mitigation |
|------|-----------|
| HttpOnly cookie with Secure flag not sent in dev HTTP | Backend must allow REFRESH_COOKIE_SECURE=false in dev, or use Vite proxy |
| 5-minute pre_auth_token expiry for 2FA | Frontend shows countdown, redirects to login on expiry |
| Rate limiting 5 req/60s on login | UI shows Retry-After countdown, disables submit button |
| Race condition on refresh (multiple 401s) | Axios interceptor queues requests during refresh |
| No CORS in backend | Vite proxy handles /api in development |
| Forgot password email enumeration | Backend always returns 202 |

## Estimate
- ~30 files created
- ~1500-2000 lines of code (TSX + CSS + TS)
- Estimated effort: 4-6 hours for a single developer
