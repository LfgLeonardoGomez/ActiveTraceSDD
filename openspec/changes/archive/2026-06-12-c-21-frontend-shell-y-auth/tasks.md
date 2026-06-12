# Tasks: C-21 frontend-shell-y-auth

> Foundation SPA shell for activia-trace — Vite 6 + React 18 + Tailwind v4 + auth + layout.
> Dependencies: C-04 (rbac), C-03 (auth-jwt-2fa) — both COMPLETED.
> Specs: [ui-components](specs/ui-components/spec.md), [auth-login](specs/auth-login/spec.md), [auth-recovery](specs/auth-recovery/spec.md), [auth-shell](specs/auth-shell/spec.md)

---

## Phase 0: Project Scaffolding

- [x] 0.1: Create `frontend/package.json`
  - Deps: react@^18.3.1, react-dom@^18.3.1, react-router-dom@^6.28.0, @tanstack/react-query@^5.62.0, react-hook-form@^7.54.0, @hookform/resolvers@^3.9.0, zod@^3.24.0, axios@^1.7.0, clsx@^2.1.0, tailwind-merge@^2.6.0, class-variance-authority@^0.7.1, lucide-react@^0.460.0
  - DevDeps: typescript@^5.6.0, vite@^6.0.0, @vitejs/plugin-react@^4.3.0, @tailwindcss/vite@^4.0.0, tailwindcss@^4.0.0, @types/react@^18.3.0, @types/react-dom@^18.3.0, vitest@^2.1.0, @testing-library/react@^16.1.0, @testing-library/jest-dom@^6.6.0, jsdom@^25.0.0
  - Scripts: dev, build (tsc -b && vite build), preview, test, test:run, typecheck (tsc --noEmit)
  - File: `frontend/package.json`

- [x] 0.2: Create `frontend/tsconfig.json` + `tsconfig.app.json` + `tsconfig.node.json`
  - Root references app + node
  - App: target ES2020, module ESNext, moduleResolution bundler, jsx react-jsx, strict true, `@/*` → `./src/*`
  - Node: target ES2022, module ESNext, moduleResolution bundler, include vite.config.ts
  - Files: `frontend/tsconfig.json`, `frontend/tsconfig.app.json`, `frontend/tsconfig.node.json`

- [x] 0.3: Create `frontend/vite.config.ts`
  - Plugins: `@vitejs/plugin-react`, `@tailwindcss/vite`
  - Resolve alias: `@` → `./src`
  - Server proxy: `/api` → `http://localhost:8000` with `changeOrigin: true`
  - File: `frontend/vite.config.ts`

- [x] 0.4: Create `frontend/index.html`
  - `<div id="root">` mount point, `<script type="module" src="/src/main.tsx">`
  - Inter font from Google Fonts (`<link>`), meta viewport, `<title>activia trace</title>`
  - File: `frontend/index.html`

- [x] 0.5: Create `.env` and `.gitignore`
  - `.env`: `VITE_API_BASE_URL=` (empty = Vite proxy in dev)
  - `.gitignore`: `node_modules/`, `dist/`, `.env.local`, `*.tsbuildinfo`
  - Files: `frontend/.env`, `frontend/.gitignore`

- [x] 0.6: Create `frontend/src/vite-env.d.ts` and `frontend/src/index.css`
  - `vite-env.d.ts`: `/// <reference types="vite/client" />`
  - `index.css`: `@import "tailwindcss"`, `@theme` block with brand colors (primary-50→900), semantic colors (success/warning/danger/info), neutral scale, semantic aliases (background, foreground, muted, border, input, ring), font families (Inter, JetBrains Mono), animation keyframes (spin, fade-in, slide-in-left), `@layer base` with body defaults
  - Files: `frontend/src/vite-env.d.ts`, `frontend/src/index.css`

---

## Phase 1: Utility Functions

- [x] 1.1: Create `src/lib/utils.ts` — `cn()` helper
  - `cn(...inputs: ClassValue[]): string` using `clsx` + `twMerge`
  - Exports: `cn` (named)
  - Spec: REQ-UI-07
  - File: `frontend/src/lib/utils.ts`

- [x] 1.2: Create `src/shared/hooks/usePermissions.ts`
  - Reads `user.roles` from `useAuth()`
  - Returns `{ can, hasPermission, hasAnyPermission }`
  - `can(perm)`: checks if any role includes `perm` in its `permissions` array
  - Spec: REQ-SHELL-05 (sidebar filtering), REQ-SHELL-03 (PermissionGuard)
  - File: `frontend/src/shared/hooks/usePermissions.ts`

---

## Phase 2: Shared UI Components

- [x] 2.1: Create `src/shared/components/ui/Button.tsx` — CVA button
  - Variants via CVA: default (primary-600 bg), destructive (danger-600 bg), outline (border), secondary (muted bg), ghost (no bg), link (inline text)
  - Sizes: default (h-9 px-4), sm (h-8 px-3 text-xs), lg (h-10 px-8), icon (h-9 w-9)
  - `isLoading` prop: disabled + Spinner before text
  - `disabled` prop: `opacity-50`, `pointer-events-none`, `aria-disabled`
  - Specs: REQ-UI-01, REQ-UI-02, REQ-UI-03
  - File: `frontend/src/shared/components/ui/Button.tsx`

- [x] 2.2: Create `src/shared/components/ui/Input.tsx` — accessible input with label + error
  - `React.forwardRef`, props: `label?`, `error?`, standard input attrs
  - Renders `<label>` with `htmlFor`, auto-generated `id` via `useId()`
  - When `error` set: `aria-invalid="true"`, red border, `<p role="alert">` message below
  - Spec: REQ-UI-04
  - File: `frontend/src/shared/components/ui/Input.tsx`

- [x] 2.3: Create `src/shared/components/ui/Card.tsx` — compound card
  - Exports: `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`
  - All `<div>` with `cn()` className composition
  - Card: bg-background, border, rounded-lg, shadow-sm
  - Spec: REQ-UI-05
  - File: `frontend/src/shared/components/ui/Card.tsx`

- [x] 2.4: Create `src/shared/components/ui/Label.tsx`
  - `<label>` with `text-sm font-medium leading-none`, `peer-disabled:` variants
  - File: `frontend/src/shared/components/ui/Label.tsx`

- [x] 2.5: Create `src/shared/components/ui/Spinner.tsx` — CSS-animated spinner
  - Props: `size?` ('sm' | 'default' | 'lg'), `className?`
  - Uses `@keyframes spin` from index.css, `border-t-transparent` arc
  - Sizes: sm=16px, default=24px, lg=32px
  - Accessible: `role="status"`, `aria-label="Cargando"`
  - Spec: REQ-UI-06
  - File: `frontend/src/shared/components/ui/Spinner.tsx`

---

## Phase 3: API Client + Auth Context

- [x] 3.1: Create `src/shared/services/api.ts` — Axios instance + interceptors
  - Module-level `accessToken` variable (NOT localStorage — XSS protection)
  - Exports: `api` (default), `setAccessToken()`, `getAccessToken()`, `clearAccessToken()`
  - Instance: `baseURL` from `VITE_API_BASE_URL`, `withCredentials: true`
  - Request interceptor: attach `Authorization: Bearer {token}` when token exists
  - Response interceptor: on 401, queue concurrent requests, POST `/api/auth/refresh` via bare axios (loop prevention), replay queue on success, hard redirect `/login` on failure
  - Specs: REQ-SHELL-11, REQ-SHELL-12, REQ-SHELL-13, REQ-SHELL-14
  - File: `frontend/src/shared/services/api.ts`

- [x] 3.2: Create `src/shared/services/AuthContext.tsx` — AuthProvider + useAuth
  - State: `user` (MeResponse | null), `accessToken` (string | null), `isAuthenticated`, `isLoading`
  - On mount: `isLoading=true`, call refresh, if success → fetch `/me` via TanStack Query, set `isAuthenticated=true`, `isLoading=false`
  - Methods: `login()`, `verify2FA()`, `logout()`
  - `login()` returns `LoginResult` discriminated union (`{ needs2FA: true, preAuthToken }` | `{ needs2FA: false, accessToken }`)
  - `logout()`: POST `/api/auth/logout`, always clear state regardless of response
  - 2FA `preAuthToken` stored in page state (NOT in AuthContext)
  - Specs: REQ-LOGIN-10, REQ-LOGIN-11, REQ-LOGIN-12, REQ-SHELL-02
  - File: `frontend/src/shared/services/AuthContext.tsx`

---

## Phase 4: Auth Types + API Services

- [x] 4.1: Create `src/features/auth/types/auth.types.ts`
  - Types: `LoginRequest`, `LoginResponse`, `TwoFactorVerifyRequest`, `TwoFactorVerifyResponse`, `MeResponse` (with `roles: Role[]`), `Role` (with `permissions: string[]`), `ForgotPasswordRequest`, `ResetPasswordRequest`, `RefreshResponse`, `LoginResult` (discriminated union)
  - File: `frontend/src/features/auth/types/auth.types.ts`

- [x] 4.2: Create `src/features/auth/services/auth.api.ts`
  - Functions: `login()`, `verify2FA()`, `logout()`, `forgotPassword()`, `resetPassword()`, `refresh()`
  - Use shared `api` instance for all except `refresh()` (uses bare `axios.post()` to avoid interceptor loop)
  - `logout()` returns void (caller clears state regardless)
  - Spec refs: All login, 2FA, recovery API contracts from design §9
  - File: `frontend/src/features/auth/services/auth.api.ts`

---

## Phase 5: Auth Hooks

- [x] 5.1: Create `src/features/auth/hooks/useLogin.ts` — `useLoginForm()`
  - React Hook Form + Zod schema: email (valid email), password (min 8)
  - Returns: `form`, `onSubmit`, `isSubmitting`, `rateLimitCountdown`, `error`, `clearError`
  - 401 handling: show "Credenciales inválidas", clear password
  - 429 handling: read `Retry-After` header, start countdown, disable submit
  - Specs: REQ-LOGIN-01, REQ-LOGIN-04, REQ-LOGIN-05
  - File: `frontend/src/features/auth/hooks/useLogin.ts`

- [x] 5.2: Create `src/features/auth/hooks/useMe.ts` — `useMeQuery()`
  - TanStack Query `useQuery` with queryKey `['me']`, calls `api.get('/api/auth/me')`
  - `staleTime: 5min`, `retry: 1`, `enabled: !!getAccessToken()`
  - Consumed internally by AuthProvider, NOT exported for general use
  - Spec: REQ-LOGIN-10
  - File: `frontend/src/features/auth/hooks/useMe.ts`

- [x] 5.3: Create `src/features/auth/hooks/useLogout.ts` — `useLogoutMutation()`
  - `useMutation({ mutationFn: logout from useAuth, onSettled: queryClient.clear() })`
  - Spec: REQ-SHELL-07
  - File: `frontend/src/features/auth/hooks/useLogout.ts`

- [x] 5.4: Create `src/features/auth/hooks/useForgotPassword.ts` — `useForgotPasswordForm()`
  - React Hook Form + Zod email validation
  - Returns: `form`, `onSubmit`, `isSubmitting`, `isSuccess`, `resendCountdown`, `error`
  - On 202: set `isSuccess=true`, start 30s resend countdown
  - Specs: REQ-RECOV-01, REQ-RECOV-02
  - File: `frontend/src/features/auth/hooks/useForgotPassword.ts`

- [x] 5.5: Create `src/features/auth/hooks/useResetPassword.ts` — `useResetPasswordForm()`
  - React Hook Form + Zod schema: `new_password` (min 8), `confirm_password` (must match via `.refine()`)
  - Reads `token` from `useSearchParams()`, redirects to `/forgot-password` if missing
  - On 204: navigate to `/login?success=password_reset`
  - On 400: show "Token inválido o expirado. Solicitá un nuevo restablecimiento."
  - Specs: REQ-RECOV-03, REQ-RECOV-04, REQ-RECOV-05, REQ-RECOV-06, REQ-RECOV-07
  - File: `frontend/src/features/auth/hooks/useResetPassword.ts`

---

## Phase 6: Auth Components

- [x] 6.1: Create `src/features/auth/components/LoginForm.tsx`
  - Props: `onSubmit`, `isSubmitting`, `error`, `rateLimitCountdown`
  - Renders: Card with title "Iniciar sesión", email + password Inputs, Button "Iniciar sesión" (or countdown text when rate-limited), Link to `/forgot-password`
  - Shows `Alert` (or styled div) for general errors
  - Specs: REQ-LOGIN-01, REQ-LOGIN-04, REQ-LOGIN-05
  - File: `frontend/src/features/auth/components/LoginForm.tsx`

- [x] 6.2: Create `src/features/auth/components/TwoFactorForm.tsx`
  - Props: `onSubmit`, `isSubmitting`, `error`
  - Renders: Card with title "Verificación en dos pasos", single Input for 6-digit TOTP (`inputMode="numeric"`, `maxLength=6`, `pattern="[0-9]*"`), Button "Verificar"
  - Zod validation: exactly 6 digits, numeric only
  - Specs: REQ-LOGIN-06, REQ-LOGIN-07, REQ-LOGIN-09
  - File: `frontend/src/features/auth/components/TwoFactorForm.tsx`

- [x] 6.3: Create `src/features/auth/components/ForgotPasswordForm.tsx`
  - Props: `onSubmit`, `isSubmitting`, `isSuccess`, `resendCountdown`
  - When `isSuccess=false`: email Input, submit button "Enviar instrucciones", link "Volver al inicio de sesión"
  - When `isSuccess=true`: success message "Si el email existe, recibirás instrucciones", disabled button with countdown "Reenviar en {seconds}s"
  - Specs: REQ-RECOV-01, REQ-RECOV-02
  - File: `frontend/src/features/auth/components/ForgotPasswordForm.tsx`

- [x] 6.4: Create `src/features/auth/components/ResetPasswordForm.tsx`
  - Props: `onSubmit`, `isSubmitting`, `error`, `onTyping`
  - Renders: Card with title "Restablecer contraseña", two password Inputs, submit button "Restablecer contraseña"
  - Error message + link "Solicitar nuevo restablecimiento" on token errors
  - Specs: REQ-RECOV-03, REQ-RECOV-04, REQ-RECOV-05, REQ-RECOV-06, REQ-RECOV-07
  - File: `frontend/src/features/auth/components/ResetPasswordForm.tsx`

---

## Phase 7: Auth Pages

- [x] 7.1: Create `src/features/auth/pages/LoginPage.tsx`
  - Reads `?error=session_expired` and `?success=password_reset` query params
  - If already authenticated → redirect to `/`
  - Renders `<LoginForm>` inside full-screen centered layout
  - On login success (no 2FA): invalidate `['me']` query, navigate to `?redirect` target or `/`
  - On `needs2FA`: navigate to `/2fa` with `state: { preAuthToken }`
  - File: `frontend/src/features/auth/pages/LoginPage.tsx`

- [x] 7.2: Create `src/features/auth/pages/TwoFactorPage.tsx`
  - Reads `preAuthToken` from `location.state`
  - If no token → redirect to `/login`
  - Renders `<TwoFactorForm>` inside centered layout
  - On success: invalidate `['me']` query, navigate to `/`
  - File: `frontend/src/features/auth/pages/TwoFactorPage.tsx`

- [x] 7.3: Create `src/features/auth/pages/ForgotPasswordPage.tsx`
  - Renders `<ForgotPasswordForm>` inside centered layout
  - File: `frontend/src/features/auth/pages/ForgotPasswordPage.tsx`

- [x] 7.4: Create `src/features/auth/pages/ResetPasswordPage.tsx`
  - Reads `token` from `useSearchParams()`
  - No token → navigate to `/forgot-password`
  - Renders `<ResetPasswordForm>` inside centered layout
  - On success → navigate to `/login?success=password_reset`
  - File: `frontend/src/features/auth/pages/ResetPasswordPage.tsx`

---

## Phase 8: Shell Layout + Guards

- [x] 8.1: Create `src/shared/components/guards/ProtectedRoute.tsx`
  - Layout route (no path, uses `<Outlet />`)
  - `isLoading` → full-screen `<Spinner />` centered with `aria-label="Cargando sesión"`
  - Not authenticated → `<Navigate to="/login" state={{ from: location }} />`
  - Authenticated → `<Outlet />`
  - Specs: REQ-SHELL-01, REQ-SHELL-02
  - File: `frontend/src/shared/components/guards/ProtectedRoute.tsx`

- [x] 8.2: Create `src/shared/components/guards/PermissionGuard.tsx`
  - Props: `requiredPermissions` (string | string[]), `requireAll?` (default true), `redirectTo?` (default '/')
  - Uses `usePermissions()` to check access
  - AND mode (default): user must have ALL permissions
  - OR mode (`requireAll=false`): user must have AT LEAST ONE
  - Check fails → `<Navigate to={redirectTo} />` + info message "No tenés permiso para acceder a esta página"
  - Spec: REQ-SHELL-03
  - File: `frontend/src/shared/components/guards/PermissionGuard.tsx`

- [x] 8.3: Create `src/shared/components/Sidebar.tsx`
  - Role-based nav items filtered by `usePermissions().can()`: Alumnos, Materias, Comisiones, Comunicación, Equipos, Liquidaciones
  - Each item: `NavLink` with lucide-react icon + label
  - Active link: `bg-primary-50 text-primary-700 font-medium`
  - Mobile: fixed overlay, `isOpen` state, backdrop click closes
  - Specs: REQ-SHELL-04, REQ-SHELL-05, REQ-SHELL-09
  - File: `frontend/src/shared/components/Sidebar.tsx`

- [x] 8.4: Create `src/shared/components/Topbar.tsx`
  - Props: `onToggleSidebar?`
  - Left: hamburger `Menu` icon (mobile) — calls `onToggleSidebar`
  - Right: user email from `useAuth()`, logout `LogOut` icon button
  - Spec: REQ-SHELL-06
  - File: `frontend/src/shared/components/Topbar.tsx`

- [x] 8.5: Create `src/shared/components/Layout.tsx`
  - Structure: flex h-screen → Sidebar + (Topbar + impersonation banner + main `<Outlet />`)
  - Impersonation banner: yellow warning, text "Estás operando como {nombre} {apellido}", "Salir de impersonación" button → POST `/api/auth/impersonation/stop`
  - Specs: REQ-SHELL-04, REQ-SHELL-09, REQ-SHELL-10
  - File: `frontend/src/shared/components/Layout.tsx`

---

## Phase 9: App Entry + Dashboard Home

- [x] 9.1: Create `src/features/auth/pages/DashboardHome.tsx`
  - Reads `user.roles` from `useAuth()`
  - Redirect priority: `/alumnos`, `/materias`, `/comisiones`, `/comunicacion`, `/equipos`, `/liquidaciones`
  - First match → `<Navigate to={route} />`
  - No match → fallback: "No tenés acceso a ningún módulo" + logout button
  - Spec: REQ-SHELL-08
  - File: `frontend/src/features/auth/pages/DashboardHome.tsx`

- [x] 9.2: Create `src/App.tsx`
  - Wraps: `QueryClientProvider` + `AuthProvider` + `BrowserRouter` + `Routes`
  - Public routes: `/login` (LoginPage), `/2fa` (TwoFactorPage), `/forgot-password` (ForgotPasswordPage), `/reset-password` (ResetPasswordPage)
  - Protected routes: `<ProtectedRoute>` → `<Layout>` → `/` (DashboardHome), `/*` (NotFound)
  - File: `frontend/src/App.tsx`

- [x] 9.3: Create `src/main.tsx`
  - `QueryClient` with defaults: `retry: 1`, `refetchOnWindowFocus: false`, `staleTime: 5min`
  - `ReactDOM.createRoot` → `<React.StrictMode>` → `<QueryClientProvider>` → `<AuthProvider>` → `<App />`
  - Import `./index.css`
  - File: `frontend/src/main.tsx`

---

## Phase 10: Tests (Optional — can defer)

- [x] 10.1: Test login auth flow — LoginForm renders, validation errors, submit triggers API
  - Setup vitest with `@testing-library/react`, wrap with form context
  - Specs: REQ-LOGIN-01 scenarios 1-4
  - File: `frontend/src/features/auth/__tests__/LoginForm.test.tsx`

- [x] 10.2: Test AuthProvider — initial state (isLoading), login sets user, logout clears
  - Mock Axios interceptor module, use `renderHook` with wrapper
  - Specs: REQ-LOGIN-12 scenarios 1-5
  - File: `frontend/src/shared/services/__tests__/AuthContext.test.tsx`

- [x] 10.3: Test ProtectedRoute — spinner while loading, redirect when unauthenticated, passes when authenticated
  - Mock `useAuth()`, render with Router
  - Specs: REQ-SHELL-01 scenarios 1-3, REQ-SHELL-02 scenarios 1-2
  - File: `frontend/src/shared/components/guards/__tests__/ProtectedRoute.test.tsx`

- [x] 10.4: Test Button component — variants render correct classes, disabled blocks clicks, loading shows spinner
  - Specs: REQ-UI-01, REQ-UI-02, REQ-UI-03
  - File: `frontend/src/shared/components/ui/__tests__/Button.test.tsx`

- [x] 10.5: Setup vitest config and test environment
  - `vitest.config.ts` with jsdom environment, `@/` alias matching vite
  - `src/test/setup.ts` — import `@testing-library/jest-dom`
  - Files: `frontend/vitest.config.ts`, `frontend/src/test/setup.ts`

---

## Summary

| Phase | Tasks | Files Created |
|-------|-------|---------------|
| 0: Scaffolding | 6 | 9 config files |
| 1: Utilities | 2 | 2 files |
| 2: UI Components | 5 | 5 components |
| 3: API + Auth Context | 2 | 2 services |
| 4: Auth Types + API | 2 | 2 files |
| 5: Auth Hooks | 5 | 5 hooks |
| 6: Auth Components | 4 | 4 components |
| 7: Auth Pages | 4 | 4 pages |
| 8: Shell Layout + Guards | 5 | 5 components |
| 9: App Entry | 3 | 3 files |
| 10: Tests (optional) | 5 | 5 test files + 2 config |
| **Total** | **43** | **~48 files** |
