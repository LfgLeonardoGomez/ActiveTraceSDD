# Design: C-21 frontend-shell-y-auth

## 1. Architecture Overview

### Development Server

Vite 6 dev server with the `@tailwindcss/vite` plugin handles everything:

| Service | URL | Notes |
|---------|-----|-------|
| Vite dev server | `http://localhost:5173` | HMR, TSX compilation |
| Vite proxy `/api` | → `http://localhost:8000` | No CORS in dev |
| Backend API | `http://localhost:8000` | FastAPI (separate process) |

The Vite proxy configuration in `vite.config.ts`:

```ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
},
```

This eliminates CORS entirely in development — the browser sees same-origin requests to the Vite origin. HttpOnly cookies (refresh token) flow through the proxy without issues.

### Production

In production (Easypanel), Nginx or the reverse proxy serves the built SPA from `frontend/dist/` and proxies `/api/*` to the FastAPI backend. The same same-origin pattern applies — no CORS needed.

### Key Technology Decisions

| Decision | Rationale |
|----------|-----------|
| **react-router-dom v6 (NOT v7)** | v7 in library mode is essentially v6 with different import paths, but v7's framework mode (loader/action/route modules) is incompatible with our AuthProvider pattern. v6 is stable, well-documented, and sufficient. |
| **Tailwind v4 CSS-first** | Tailwind v4 replaces `tailwind.config.js` with `@theme` directives in CSS. No PostCSS, no `tailwind.config.js`, no `postcss.config.js`. The Vite plugin `@tailwindcss/vite` handles everything. |
| **In-memory token (not localStorage)** | Access token stored in a module closure variable inside the Axios interceptor module. Invisible to XSS. No `localStorage`, no `sessionStorage`. |
| **HttpOnly refresh cookie** | Refresh token in an HttpOnly cookie with `path=/api/auth/refresh`. JS cannot read it. The interceptor only calls the refresh endpoint; the browser sends the cookie automatically. |
| **TanStack Query for /me** | The user profile is fetched via TanStack Query from `GET /api/auth/me`, with appropriate `staleTime` to avoid redundant refetches while keeping the UI responsive. |

### Component Architecture Pattern

All shared UI components follow the **CVA (class-variance-authority)** pattern: a base `cva()` call defines variants, and the component accepts `variant` and `size` props. This is the same pattern used by shadcn/ui (though we don't use shadcn/ui itself).

Auth feature components follow the **container/presentational** pattern: Page components are containers that use hooks for data/actions, Form components are presentational and receive callbacks.

### Directory Layout

```
frontend/
├── index.html                    # SPA entry HTML (Vite root)
├── package.json
├── tsconfig.json                 # Project references to tsconfig.app.json + tsconfig.node.json
├── tsconfig.app.json             # App compilation config
├── tsconfig.node.json            # Node/Vite config compilation config
├── vite.config.ts                # Vite config with @tailwindcss/vite + @vitejs/plugin-react
├── .env                          # VITE_API_BASE_URL (optional, defaults to "" for Vite proxy)
├── src/
│   ├── main.tsx                  # ReactDOM.createRoot, providers wrapping
│   ├── App.tsx                   # Route definitions
│   ├── index.css                 # @import "tailwindcss" + @theme block + base layer
│   ├── vite-env.d.ts             # Vite client types reference
│   ├── lib/
│   │   └── utils.ts              # cn() helper (clsx + twMerge)
│   ├── features/
│   │   └── auth/
│   │       ├── types/
│   │       │   └── auth.types.ts        # LoginRequest, LoginResponse, MeResponse, etc.
│   │       ├── services/
│   │       │   └── auth.api.ts          # login(), verify2FA(), logout(), forgot(), reset(), refresh()
│   │       ├── hooks/
│   │       │   ├── useLogin.ts          # mutation hook wrapping auth.api.login
│   │       │   ├── useMe.ts             # TanStack Query hook for GET /api/auth/me
│   │       │   ├── useLogout.ts         # mutation hook wrapping auth.api.logout
│   │       │   ├── useForgotPassword.ts # mutation hook for forgot-password
│   │       │   └── useResetPassword.ts  # mutation hook for reset-password
│   │       ├── components/
│   │       │   ├── LoginForm.tsx         # Email + password form
│   │       │   ├── TwoFactorForm.tsx     # 6-digit TOTP form
│   │       │   ├── ForgotPasswordForm.tsx # Email form for forgot flow
│   │       │   └── ResetPasswordForm.tsx  # New password + confirm form
│   │       └── pages/
│   │           ├── LoginPage.tsx         # Container: renders LoginForm + handles errors
│   │           ├── TwoFactorPage.tsx     # Container: renders TwoFactorForm + handles pre_auth
│   │           ├── ForgotPasswordPage.tsx # Container: renders ForgotPasswordForm
│   │           ├── ResetPasswordPage.tsx # Container: reads token from URL, renders ResetPasswordForm
│   │           └── DashboardHome.tsx     # Landing page (redirect based on roles)
│   └── shared/
│       ├── services/
│       │   ├── api.ts             # Axios instance + interceptors + module-level token variable
│       │   └── AuthContext.tsx     # AuthProvider + useAuth hook + AuthState interface
│       ├── components/
│       │   ├── ui/
│       │   │   ├── Button.tsx      # CVA button with variants/sizes/loading
│       │   │   ├── Input.tsx       # Input with label + error + forwarded ref
│       │   │   ├── Card.tsx        # Compound card (Card, CardHeader, CardTitle, etc.)
│       │   │   ├── Label.tsx       # Accessible label component
│       │   │   └── Spinner.tsx     # CSS-animated spinner
│       │   ├── Layout.tsx          # Sidebar + Topbar + Outlet + impersonation banner
│       │   ├── Sidebar.tsx         # Navigation links based on user roles
│       │   ├── Topbar.tsx          # User email + logout + mobile menu toggle
│       │   └── guards/
│       │       ├── ProtectedRoute.tsx   # Checks isAuthenticated, redirects to /login
│       │       └── PermissionGuard.tsx  # Checks roles, redirects to /
│       └── hooks/
│           └── usePermissions.ts  # Derives UI capabilities from user.roles
```

---

## 2. Component Tree

```
<App>
  <QueryClientProvider>           ← TanStack Query provider
    <AuthProvider>                 ← React Context: user, token, login/logout/verify2FA
      <BrowserRouter>
        <Routes>
          {/* Public routes — no layout, full-screen */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/2fa" element={<TwoFactorPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />

          {/* Protected routes — wrapped in Layout */}
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/" element={<DashboardHome />} />
              {/* Future: C-22, C-23, C-24 features */}
            </Route>
          </Route>

          {/* 404 */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  </QueryClientProvider>
</App>
```

### Router structure rationale

- **Public routes** render full-screen forms without the sidebar/topbar layout. Auth pages are standalone.
- **ProtectedRoute** is a layout route (no `path`, uses `<Outlet>`) that checks `isAuthenticated`. If false, redirects to `/login` preserving the `?redirect=` param.
- **Layout** is also a layout route: renders `<Sidebar />` + `<Topbar />` + `<Outlet />` for the main content.
- **DashboardHome** at `/` performs the role-based redirect (REQ-SHELL-08).

---

## 3. Auth Flow (State Machine)

```
                         ┌──────────────────────┐
                         │  App Mount / Tab Open  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                     ┌──────────────────────────┐
                     │  isLoading = true         │
                     │  Show full-screen Spinner │
                     │  POST /api/auth/refresh   │
                     └──────────┬───────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
               success                     fail
                    │                       │
                    ▼                       ▼
         ┌────────────────────┐   ┌────────────────────┐
         │ Set accessToken    │   │ isLoading = false   │
         │ GET /api/auth/me   │   │ isAuthenticated =   │
         │ isLoading = false  │   │   false             │
         │ isAuthenticated =  │   │ Show /login         │
         │   true             │   └────────────────────┘
         │ Show <Layout />    │
         └────────────────────┘


                       ┌──────────┐
                       │  /login   │
                       └────┬─────┘
                            │
                     submit email+password
                            │
                            ▼
                   POST /api/auth/login
                            │
               ┌────────────┴────────────┐
               │                         │
            200 (no 2FA)             200 (needs 2FA)
               │                         │
               ▼                         ▼
       ┌──────────────────┐    ┌─────────────────────┐
       │ Set accessToken   │    │ Store preAuthToken  │
       │ GET /api/auth/me  │    │ Navigate to /2fa    │
       │ Navigate to /     │    └──────────┬──────────┘
       │ (or ?redirect)    │               │
       └──────────────────┘               │
                                     submit code
                                           │
                                           ▼
                                  POST /api/auth/2fa/verify
                                           │
                               ┌───────────┴───────────┐
                               │                       │
                            200                     401 (expired)
                               │                       │
                               ▼                       ▼
                       ┌──────────────┐      ┌──────────────────────┐
                       │ Set token    │      │ Clear preAuthToken   │
                       │ GET /me      │      │ Redirect to /login   │
                       │ Navigate /   │      │ "Sesión expirada"    │
                       └──────────────┘      └──────────────────────┘


                       ┌──────────┐
                       │  Logout  │
                       └────┬─────┘
                            │
                     POST /api/auth/logout
                            │
               (always, regardless of response)
                            │
                            ▼
               ┌──────────────────────┐
               │ Clear accessToken    │
               │ user = null          │
               │ isAuthenticated=false│
               │ Navigate to /login   │
               └──────────────────────┘
```

---

## 4. AuthProvider Interface

### AuthState interface (consumed via `useAuth()`)

```typescript
interface AuthState {
  user: MeResponse | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  login(email: string, password: string): Promise<LoginResult>;
  verify2FA(preAuthToken: string, code: string): Promise<void>;
  logout(): Promise<void>;
}
```

### LoginResult discriminated union

```typescript
type LoginResult =
  | { needs2FA: true; preAuthToken: string }
  | { needs2FA: false; accessToken: string };
```

### AuthProvider behavior on mount

1. Set `isLoading = true`
2. Call `refresh()` (POST `{baseURL}/auth/refresh` — note: this goes to the Axios instance without auth interceptor to avoid circular dependency)
3. If refresh succeeds:
   - Store the new `accessToken` in the module variable (via `setAccessToken()` from `api.ts`)
   - Call `GET /api/auth/me` (TanStack Query)
   - Set `isAuthenticated = true`
4. If refresh fails (401 or network error):
   - Set `isAuthenticated = false`
5. Set `isLoading = false`

### login() behavior

1. Call `POST /api/auth/login` with `{ email, password }`
2. If response includes `access_token` → no 2FA:
   - Call `setAccessToken(accessToken)` in the Axios module
   - Return `{ needs2FA: false, accessToken }`
   - The consuming component (LoginPage) calls `queryClient.invalidateQueries('me')` to trigger the `/me` fetch
   - Navigate to redirect target
3. If response includes `pre_auth_token` → 2FA required:
   - Store `preAuthToken` in component state (page-scoped, not context)
   - Return `{ needs2FA: true, preAuthToken }`
   - LoginPage navigates to `/2fa`

### verify2FA() behavior

1. Call `POST /api/auth/2fa/verify` with `{ pre_auth_token, code }`
2. If success:
   - Call `setAccessToken(accessToken)` in the Axios module
   - Invalidate `/me` query
   - Navigate to `/`
3. If 401:
   - Clear `preAuthToken`
   - Navigate to `/login` with error "Sesión expirada"
4. If 400 (invalid code):
   - Return error message "Código inválido"

### logout() behavior

1. Call `POST /api/auth/logout`
2. Regardless of response:
   - Call `clearAccessToken()` in the Axios module
   - Set `user = null`, `isAuthenticated = false`
   - Navigate to `/login`

### Why TanStack Query for /me instead of React state?

The `/me` response is consumed by multiple components (Sidebar for navigation links, Topbar for user info, PermissionGuard for role checks). TanStack Query:
- Caches the response and deduplicates requests
- `staleTime: 5 * 60 * 1000` (5 min) avoids refetching on every route change
- `gcTime: 30 * 60 * 1000` (30 min) keeps data in cache for tab-switching
- `retry: 1` retries once on failure
- Invalidated on login/logout

---

## 5. Axios Interceptor Architecture

### In-memory token store

```typescript
// Module-level variable — invisible to XSS, not persisted to storage
let accessToken: string | null = null;

// Exported setters for AuthProvider
export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

export function clearAccessToken(): void {
  accessToken = null;
}
```

### Axios instance

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '',
  withCredentials: true,                    // send HttpOnly refresh cookie
  headers: { 'Content-Type': 'application/json' },
});
```

### Request interceptor

```typescript
api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});
```

### Response interceptor (transparent refresh)

```typescript
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}> = [];

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Only attempt refresh on 401, and only once per request
    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    // If a refresh is already in flight, queue this request
    if (isRefreshing) {
      return new Promise<string>((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then((token) => {
        originalRequest.headers.Authorization = `Bearer ${token}`;
        return api(originalRequest);
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      // POST to refresh endpoint — cookie is sent automatically via withCredentials
      const { data } = await axios.post(
        `${import.meta.env.VITE_API_BASE_URL ?? ''}/api/auth/refresh`,
        {},
        { withCredentials: true },
      );

      const newToken: string = data.access_token;
      setAccessToken(newToken);

      // Replay queued requests
      failedQueue.forEach(({ resolve }) => resolve(newToken));
      failedQueue = [];

      // Retry the original request
      originalRequest.headers.Authorization = `Bearer ${newToken}`;
      return api(originalRequest);
    } catch (refreshError) {
      // Reject all queued requests
      failedQueue.forEach(({ reject }) => reject(refreshError));
      failedQueue = [];

      clearAccessToken();
      window.location.href = '/login';    // hard redirect — clears React state

      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  },
);
```

### Queue mechanism detail

The `failedQueue` array stores promise `resolve`/`reject` pairs for every request that arrives during a refresh. When the refresh completes, all queued requests are resolved with the new token, which chains into retrying the original request. If the refresh fails, all queued requests are rejected.

This prevents the **thundering herd** problem where 10 simultaneous 401s would trigger 10 refresh calls. Only 1 refresh call is made, and all 10 original requests are retried once the new token is available.

### Important: refresh endpoint uses a SEPARATE axios instance

The refresh call uses a bare `axios.post()` rather than the `api` instance to avoid infinite loops: if the refresh endpoint itself returns 401 (expired cookie), the interceptor would try to refresh the refresh, causing a loop.

---

## 6. File-by-File Implementation Plan

### Config files

#### 1. `frontend/package.json`

**Purpose**: Project manifest with all dependencies and scripts.

**Key dependencies**:
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.28.0",
    "@tanstack/react-query": "^5.62.0",
    "react-hook-form": "^7.54.0",
    "@hookform/resolvers": "^3.9.0",
    "zod": "^3.24.0",
    "axios": "^1.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.6.0",
    "class-variance-authority": "^0.7.1",
    "lucide-react": "^0.460.0"
  },
  "devDependencies": {
    "typescript": "^5.6.0",
    "vite": "^6.0.0",
    "@vitejs/plugin-react": "^4.3.0",
    "@tailwindcss/vite": "^4.0.0",
    "tailwindcss": "^4.0.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "vitest": "^2.1.0",
    "@testing-library/react": "^16.1.0",
    "@testing-library/jest-dom": "^6.6.0",
    "jsdom": "^25.0.0"
  },
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:run": "vitest run",
    "typecheck": "tsc --noEmit"
  }
}
```

---

#### 2. `frontend/tsconfig.json`

**Purpose**: Root tsconfig with project references to `tsconfig.app.json` and `tsconfig.node.json`.

```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

---

#### 3. `frontend/tsconfig.app.json`

**Purpose**: TypeScript compilation config for the application source code.

**Key settings**:
- `compilerOptions.target`: `ES2020`
- `compilerOptions.module`: `ESNext`
- `compilerOptions.moduleResolution`: `bundler` (Vite handles resolution)
- `compilerOptions.jsx`: `react-jsx`
- `compilerOptions.strict`: `true`
- `compilerOptions.paths`: `{ "@/*": ["./src/*"] }`
- `include`: `["src"]`

---

#### 4. `frontend/tsconfig.node.json`

**Purpose**: TypeScript config for Vite config file and other Node-side files.

**Key settings**:
- `compilerOptions.target`: `ES2022`
- `compilerOptions.module`: `ESNext`
- `compilerOptions.moduleResolution`: `bundler`
- `include`: `["vite.config.ts"]`

---

#### 5. `frontend/vite.config.ts`

**Purpose**: Vite configuration.

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

---

#### 6. `frontend/index.html`

**Purpose**: SPA entry HTML.

Key elements:
- `<script type="module" src="/src/main.tsx">` — Vite entry point
- `<div id="root">` — React mount point
- `<link rel="icon">` placeholder
- `<title>activia trace</title>`
- Meta viewport tag for responsive layout

---

#### 7. `frontend/.env`

**Purpose**: Environment variables.

```env
VITE_API_BASE_URL=
```

Empty string means the Axios instance uses relative URLs, which hit the Vite proxy in dev. In production, set `VITE_API_BASE_URL=https://api.activia-trace.com` or leave empty if the SPA is served from the same domain.

---

#### 8. `frontend/.gitignore`

```
node_modules/
dist/
.env.local
*.tsbuildinfo
```

---

### Entry points

#### 9. `frontend/src/main.tsx`

**Purpose**: Application bootstrap.

```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/shared/services/AuthContext';
import App from './App';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);
```

---

#### 10. `frontend/src/App.tsx`

**Purpose**: Route definitions (see Component Tree in §2).

Key exports: `App` (default).

**Data flow**: Reads `isAuthenticated` from `useAuth()` to decide routes? No — `ProtectedRoute` does this. App.tsx just defines the route structure.

---

#### 11. `frontend/src/index.css`

**Purpose**: Global styles — Tailwind import, `@theme` block, base layer, utility animations.

See §7 for the full `@theme` configuration.

Contains:
1. `@import "tailwindcss";` — Tailwind v4 entry point
2. `@theme { ... }` — Design tokens (colors, fonts, animations)
3. `@layer base { ... }` — Base styles (body font, background color)
4. Custom animation keyframes for spinner and fade-in
5. `@utility` blocks for reusable patterns (optional)

---

#### 12. `frontend/src/vite-env.d.ts`

**Purpose**: Vite client type declarations.

```typescript
/// <reference types="vite/client" />
```

---

### Utilities

#### 13. `frontend/src/lib/utils.ts`

**Purpose**: `cn()` helper for conditional Tailwind class merging.

```typescript
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
```

**Exports**: `cn()`

**Dependencies**: `clsx`, `tailwind-merge`

---

### Shared services

#### 14. `frontend/src/shared/services/api.ts`

**Purpose**: Centralized Axios instance with token management and interceptors.

**Exports**:
- `api` — Axios instance (default export)
- `setAccessToken(token: string | null): void`
- `getAccessToken(): string | null`
- `clearAccessToken(): void`

**Data flow**: The `api` instance is the sole HTTP client for ALL data fetching in the application. No component creates raw Axios instances. `setAccessToken` / `clearAccessToken` are called by AuthProvider after login/logout/refresh.

**Dependencies**: `axios`

**Why module variable instead of React Context?**: The Axios module is outside React's component tree. It needs to read the token synchronously in the request interceptor. A React Context would require passing it through every API call, which is impractical. The module variable is set by AuthProvider after mount and updated on refresh.

---

#### 15. `frontend/src/shared/services/AuthContext.tsx`

**Purpose**: React Context that provides auth state and actions to the entire app.

**Exports**:
- `AuthProvider` (named export) — wraps children with context
- `useAuth()` (named export) — hook to access auth state and actions
- `AuthState` interface (see §4)

**Internal state**:
- `user: MeResponse | null` — from `useMe` TanStack Query
- `accessToken: string | null` — from `api.getAccessToken()`
- `isAuthenticated: boolean`
- `isLoading: boolean`

**Key implementation details**:
- On mount: set `isLoading = true`, call refresh endpoint, then fetch `/me`
- `login()` calls `auth.api.login()`, handles the `LoginResult` discriminated union
- `verify2FA()` calls `auth.api.verify2FA()`
- `logout()` calls `auth.api.logout()`, always clears state
- The `preAuthToken` for 2FA is stored in the LoginPage/TwoFactorPage component state, NOT in AuthContext (it's ephemeral and page-scoped)

**Dependencies**: `api.ts`, `features/auth/services/auth.api.ts`

---

### Shared components — UI primitives

#### 16. `frontend/src/shared/components/ui/Button.tsx`

**Purpose**: Versatile button with CVA variants.

**Props**:
```typescript
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
  size?: 'default' | 'sm' | 'lg' | 'icon';
  isLoading?: boolean;
}
```

**Exports**: `Button` (default)

**Variants (CVA definition)**:
- `default` — `bg-primary-600 text-white hover:bg-primary-700`
- `destructive` — `bg-danger-600 text-white hover:bg-danger-700`
- `outline` — `border border-input bg-transparent hover:bg-muted`
- `secondary` — `bg-secondary-100 text-secondary-900 hover:bg-secondary-200`
- `ghost` — `hover:bg-muted hover:text-foreground`
- `link` — `text-primary underline-offset-4 hover:underline`

**Sizes**:
- `default` — `h-9 px-4 py-2`
- `sm` — `h-8 px-3 text-xs`
- `lg` — `h-10 px-8`
- `icon` — `h-9 w-9`

**Loading state**: When `isLoading=true`, button is disabled, shows a small `<Spinner />` before text.

**Dependencies**: `cn()`, CVA

---

#### 17. `frontend/src/shared/components/ui/Input.tsx`

**Purpose**: Accessible input field with label and error message.

**Props**:
```typescript
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}
```

**Exports**: `Input` (default), forwarded ref via `React.forwardRef`

**Behavior**:
- Renders `<label>` with `htmlFor={id}` when `label` prop provided
- Renders `<input>` with generated `id` (from `useId()` or label-derived)
- When `error` is set: `aria-invalid="true"`, border is red, `<p role="alert">` shows error
- When `error` is cleared: removes alert, resets border

**Dependencies**: `cn()`

---

#### 18. `frontend/src/shared/components/ui/Card.tsx`

**Purpose**: Compound card component.

**Exports**:
- `Card` — container with border, rounded corners, shadow, bg-white
- `CardHeader` — top section with flex layout
- `CardTitle` — `text-lg font-semibold`
- `CardDescription` — `text-sm text-muted-foreground`
- `CardContent` — main content with `p-6`
- `CardFooter` — bottom section with flex, border-t

All are `<div>` elements with appropriate className via `cn()`.

**Dependencies**: `cn()`

---

#### 19. `frontend/src/shared/components/ui/Label.tsx`

**Purpose**: Accessible label.

```typescript
interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {}
```

**Exports**: `Label` (default)

Adds `text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70` styling. The `peer-disabled` variant pairs with Input's peer class.

**Dependencies**: `cn()`

---

#### 20. `frontend/src/shared/components/ui/Spinner.tsx`

**Purpose**: CSS-animated loading spinner.

**Props**:
```typescript
interface SpinnerProps {
  size?: 'sm' | 'default' | 'lg';
  className?: string;
}
```

**Exports**: `Spinner` (default)

**Sizes**:
- `sm` — `h-4 w-4 border-2`
- `default` — `h-6 w-6 border-2`
- `lg` — `h-8 w-8 border-3`

Uses `@keyframes spin` (from index.css) with a `border-t-transparent` arc to create the spinning effect. Uses `currentColor` so it inherits text color.

**Accessibility**: `aria-label="Cargando"`, `role="status"`

**Dependencies**: `cn()`

---

### Shared components — Layout

#### 21. `frontend/src/shared/components/Layout.tsx`

**Purpose**: Main application shell.

**Structure**:
```
<div className="flex h-screen">
  <Sidebar />
  <div className="flex flex-1 flex-col">
    <Topbar />
    {isImpersonating && <ImpersonationBanner />}
    <main className="flex-1 overflow-y-auto p-6">
      <Outlet />
    </main>
  </div>
</div>
```

**Exports**: `Layout` (default)

**Dependencies**: `Sidebar`, `Topbar`, `Outlet` (react-router-dom), `useAuth()`

**Impersonation banner**: Reads `user.is_impersonating` from auth context. If true, shows a yellow banner with "Estás operando como {nombre} {apellido}" and a "Salir de impersonación" button that calls `POST /api/auth/impersonation/stop`.

---

#### 22. `frontend/src/shared/components/Sidebar.tsx`

**Purpose**: Navigation sidebar with role-based links.

**State**:
- `isOpen: boolean` — mobile toggle state (default `false`)
- Navigation items derived from `usePermissions()` hook

**Navigation items definition**:
```typescript
interface NavItem {
  label: string;
  path: string;
  icon: LucideIcon;
  permission: string;      // required permission
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Alumnos', path: '/alumnos', icon: Users, permission: 'alumnos:read' },
  { label: 'Materias', path: '/materias', icon: BookOpen, permission: 'materias:read' },
  { label: 'Comisiones', path: '/comisiones', icon: LayoutGrid, permission: 'comisiones:read' },
  { label: 'Comunicación', path: '/comunicacion', icon: Mail, permission: 'comunicacion:read' },
  { label: 'Equipos', path: '/equipos', icon: UsersRound, permission: 'equipos:read' },
  { label: 'Liquidaciones', path: '/liquidaciones', icon: DollarSign, permission: 'liquidaciones:read' },
];
```

Items are filtered by checking `hasPermission(item.permission)`.

**Active link**: Uses `useLocation().pathname` to determine active state. Active link gets `bg-primary-50 text-primary-700 font-medium` styling.

**Mobile**: On `<1024px`, sidebar is a fixed overlay with backdrop. `isOpen` prop toggled by Topbar hamburger button.

**Dependencies**: `usePermissions()`, `useAuth()`, `NavLink` (react-router-dom), `lucide-react` icons

---

#### 23. `frontend/src/shared/components/Topbar.tsx`

**Purpose**: Top bar showing user info and logout.

**Content**:
- Left: hamburger menu icon on mobile (`<Menu />` from lucide-react) — calls `onToggleSidebar` prop
- Right: user email (from `useAuth().user.email`), logout button (`<LogOut />` icon)

**Exports**: `Topbar` (default)

**Props**:
```typescript
interface TopbarProps {
  onToggleSidebar?: () => void;
}
```

**Dependencies**: `useAuth()`

---

#### 24. `frontend/src/shared/components/guards/ProtectedRoute.tsx`

**Purpose**: Route guard that redirects unauthenticated users.

**Props**: None (uses `<Outlet />` as a layout route)

**Behavior**:
1. Read `isAuthenticated`, `isLoading` from `useAuth()`
2. If `isLoading` → render full-screen `<Spinner />` (centered in viewport)
3. If not `isLoading` and not `isAuthenticated` → `<Navigate to="/login" state={{ from: location }} />`
4. If authenticated → render `<Outlet />`

**Exports**: `ProtectedRoute` (default)

**Dependencies**: `useAuth()`, `Navigate` + `useLocation` (react-router-dom)

---

#### 25. `frontend/src/shared/components/guards/PermissionGuard.tsx`

**Purpose**: Route guard that checks user roles.

**Props**:
```typescript
interface PermissionGuardProps {
  requiredPermissions: string | string[];   // single or multiple permissions
  requireAll?: boolean;                      // true = AND, false = OR (default: true)
  redirectTo?: string;                       // default: '/'
  children?: React.ReactNode;
}
```

**Behavior**:
1. Read `user.roles` from `useAuth()`
2. If `requireAll` (default): user must have ALL permissions
3. If `!requireAll`: user must have AT LEAST ONE permission
4. If check fails → `<Navigate to={redirectTo} />` + shows toast "No tenés permiso"
5. If check passes → render `children` or `<Outlet />`

**Exports**: `PermissionGuard` (default)

**Dependencies**: `useAuth()`, `Navigate` (react-router-dom), `usePermissions()`

---

### Shared hooks

#### 26. `frontend/src/shared/hooks/usePermissions.ts`

**Purpose**: Derives UI-level permission checks from user roles.

**Exports**: `usePermissions()` — returns `{ can, hasPermission, hasAnyPermission }`

```typescript
interface UsePermissionsReturn {
  can: (permission: string) => boolean;       // exact permission check
  hasPermission: (permission: string) => boolean;  // alias
  hasAnyPermission: (permissions: string[]) => boolean;  // OR check — at least one
}
```

**Implementation**: Reads `user.roles` from `useAuth()`. The `MeResponse.roles` is expected to be an array of role objects, each role having a `permissions` field (array of strings like `"alumnos:read"`).

```typescript
// Expected shape from /api/auth/me
interface Role {
  id: string;
  name: string;
  permissions: string[];
}
```

`can(perm)` checks if any role in `user.roles` includes `perm` in its `permissions` array.

**Dependencies**: `useAuth()`

---

### Auth feature — Types

#### 27. `frontend/src/features/auth/types/auth.types.ts`

**Purpose**: Shared types for the auth domain.

**Exports**:
```typescript
interface LoginRequest {
  email: string;
  password: string;
}

interface LoginResponse {
  access_token?: string;       // present when no 2FA
  pre_auth_token?: string;     // present when 2FA required
  token_type?: string;
}

interface TwoFactorVerifyRequest {
  pre_auth_token: string;
  code: string;
}

interface TwoFactorVerifyResponse {
  access_token: string;
  token_type: string;
}

interface MeResponse {
  id: string;
  email: string;
  nombre: string;
  apellido: string;
  roles: Role[];
  tenant_id: string;
  is_impersonating: boolean;
}

interface Role {
  id: string;
  name: string;
  permissions: string[];
}

interface ForgotPasswordRequest {
  email: string;
}

interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

interface RefreshResponse {
  access_token: string;
  token_type: string;
}

interface LoginResult =
  | { needs2FA: true; preAuthToken: string }
  | { needs2FA: false; accessToken: string };
```

---

### Auth feature — Services

#### 28. `frontend/src/features/auth/services/auth.api.ts`

**Purpose**: API call functions for all auth endpoints.

**Exports**:
```typescript
export async function login(data: LoginRequest): Promise<LoginResponse>;
export async function verify2FA(data: TwoFactorVerifyRequest): Promise<TwoFactorVerifyResponse>;
export async function logout(): Promise<void>;
export async function forgotPassword(data: ForgotPasswordRequest): Promise<void>;
export async function resetPassword(data: ResetPasswordRequest): Promise<void>;
export async function refresh(): Promise<RefreshResponse>;
```

Each function uses the shared `api` instance from `@/shared/services/api`.

**refresh()** — Uses a bare `axios.post()` (NOT the `api` instance) to avoid interceptor loops. Same `withCredentials: true`.

**logout()** — Always returns void. The caller clears state regardless of response.

**Dependencies**: `api` from `@/shared/services/api.ts`, `axios` (for refresh)

---

### Auth feature — Hooks

#### 29. `frontend/src/features/auth/hooks/useLogin.ts`

**Purpose**: React Hook Form management for login form.

**Exports**: `useLoginForm()` — returns form methods + submit handler

```typescript
interface UseLoginFormReturn {
  form: UseFormReturn<LoginFormValues>;
  onSubmit: (e?: React.BaseSyntheticEvent) => Promise<void>;
  isSubmitting: boolean;
  rateLimitCountdown: number | null;
  error: string | null;
  clearError: () => void;
}
```

**Validation schema**:
```typescript
const loginSchema = z.object({
  email: z.string().email('Email inválido'),
  password: z.string().min(8, 'La contraseña debe tener al menos 8 caracteres'),
});
```

**Rate limiting**: Catches 429 errors, reads `Retry-After` header (or defaults to 60s), starts countdown via `setInterval`.

**Error handling**: 401 → "Credenciales inválidas", clears password field. Network error → "Error de conexión. Intentá de nuevo."

**Dependencies**: `react-hook-form`, `zod`, `@hookform/resolvers/zod`, `auth.api.login()`, `useAuth()`

---

#### 30. `frontend/src/features/auth/hooks/useMe.ts`

**Purpose**: TanStack Query hook for fetching current user.

**Exports**: `useMeQuery(options?)` — returns `UseQueryResult<MeResponse>`

```typescript
export function useMeQuery() {
  return useQuery<MeResponse>({
    queryKey: ['me'],
    queryFn: async () => {
      const { data } = await api.get('/api/auth/me');
      return data;
    },
    staleTime: 5 * 60 * 1000,
    retry: 1,
    enabled: !!getAccessToken(),  // only fetch if we have a token
  });
}
```

**Note**: This hook is consumed internally by `AuthProvider` and by `usePermissions()`. It is NOT exported for general use; components use `useAuth().user` instead.

**Dependencies**: `@tanstack/react-query`, `api` from `@/shared/services/api`

---

#### 31. `frontend/src/features/auth/hooks/useLogout.ts`

**Purpose**: Mutation hook for logout.

**Exports**: `useLogoutMutation()` — returns mutation object

```typescript
export function useLogoutMutation() {
  const { logout } = useAuth();
  return useMutation({
    mutationFn: logout,
    onSettled: () => {
      // Clear any cached queries
      queryClient.clear();
    },
  });
}
```

**Dependencies**: `@tanstack/react-query`, `useAuth()`

---

#### 32. `frontend/src/features/auth/hooks/useForgotPassword.ts`

**Purpose**: Hook managing forgot-password form state + API call.

**Exports**: `useForgotPasswordForm()` — returns form methods

```typescript
interface UseForgotPasswordFormReturn {
  form: UseFormReturn<ForgotPasswordFormValues>;
  onSubmit: (e?: React.BaseSyntheticEvent) => Promise<void>;
  isSubmitting: boolean;
  isSuccess: boolean;         // true after API returns 202
  resendCountdown: number | null;  // null | seconds remaining
  error: string | null;
}
```

**Validation**: `z.string().email('Email inválido')`

**Behavior**:
- On 202: set `isSuccess = true`, start resend countdown (30s)
- The same success message is shown regardless of whether the email exists (anti-enumeration)

**Dependencies**: `react-hook-form`, `zod`, `@hookform/resolvers/zod`, `auth.api.forgotPassword()`

---

#### 33. `frontend/src/features/auth/hooks/useResetPassword.ts`

**Purpose**: Hook managing reset-password form state + API call.

**Exports**: `useResetPasswordForm()` — returns form methods

```typescript
interface UseResetPasswordFormReturn {
  form: UseFormReturn<ResetPasswordFormValues>;
  onSubmit: (e?: React.BaseSyntheticEvent) => Promise<void>;
  isSubmitting: boolean;
  isSuccess: boolean;
  error: string | null;
  token: string;   // from URL query param
}
```

**Validation schema**:
```typescript
const resetSchema = z.object({
  new_password: z.string().min(8, 'La contraseña debe tener al menos 8 caracteres'),
  confirm_password: z.string(),
}).refine((data) => data.new_password === data.confirm_password, {
  message: 'Las contraseñas no coinciden',
  path: ['confirm_password'],
});
```

**Token extraction**: Reads `token` from `useSearchParams()` on mount. If missing, navigates to `/forgot-password`.

**Behavior**:
- On 204: set `isSuccess = true`, navigate to `/login` with success message
- On 400: show "Token inválido o expirado. Solicitá un nuevo restablecimiento."
- Error clears when user starts typing

**Dependencies**: `react-hook-form`, `zod`, `@hookform/resolvers/zod`, `auth.api.resetPassword()`

---

### Auth feature — Components

#### 34. `frontend/src/features/auth/components/LoginForm.tsx`

**Purpose**: Presentational login form.

**Props**:
```typescript
interface LoginFormProps {
  onSubmit: (values: LoginFormValues) => Promise<void>;
  isSubmitting: boolean;
  error: string | null;
  rateLimitCountdown: number | null;
}
```

**Structure**:
```
<Card className="w-full max-w-md">
  <CardHeader>
    <CardTitle>Iniciar sesión</CardTitle>
    <CardDescription>Ingresá tus credenciales para acceder a trace</CardDescription>
  </CardHeader>
  <CardContent>
    <form onSubmit={handleSubmit(onSubmit)}>
      {error && <Alert variant="destructive">{error}</Alert>}
      <Input label="Email" type="email" {...register('email')} error={errors.email?.message} />
      <Input label="Contraseña" type="password" {...register('password')} error={errors.password?.message} />
      <Button type="submit" isLoading={isSubmitting} disabled={rateLimitCountdown !== null} className="w-full">
        {rateLimitCountdown !== null
          ? `Esperá ${rateLimitCountdown}s`
          : 'Iniciar sesión'}
      </Button>
    </form>
  </CardContent>
  <CardFooter>
    <Link to="/forgot-password">¿Olvidaste tu contraseña?</Link>
  </CardFooter>
</Card>
```

**Dependencies**: `Card`, `Input`, `Button`, `Link` (react-router-dom)

---

#### 35. `frontend/src/features/auth/components/TwoFactorForm.tsx`

**Purpose**: 6-digit TOTP input.

**Props**:
```typescript
interface TwoFactorFormProps {
  onSubmit: (code: string) => Promise<void>;
  isSubmitting: boolean;
  error: string | null;
}
```

**Structure**:
```
<Card className="w-full max-w-sm">
  <CardHeader>
    <CardTitle>Verificación en dos pasos</CardTitle>
    <CardDescription>Ingresá el código de 6 dígitos de tu aplicación autenticadora</CardDescription>
  </CardHeader>
  <CardContent>
    <form onSubmit={...}>
      {error && <Alert variant="destructive">{error}</Alert>}
      <Input
        label="Código de verificación"
        maxLength={6}
        inputMode="numeric"
        pattern="[0-9]*"
        {...register('code')}
        error={errors.code?.message}
      />
      <Button type="submit" isLoading={isSubmitting} className="w-full">
        Verificar
      </Button>
    </form>
  </CardContent>
</Card>
```

**Validation**: Zod refinement for exactly 6 digits: `z.string().length(6, 'El código debe tener 6 dígitos').regex(/^\d+$/, 'El código debe ser numérico')`

**Dependencies**: `Card`, `Input`, `Button`

---

#### 36. `frontend/src/features/auth/components/ForgotPasswordForm.tsx`

**Purpose**: Email input for forgot-password flow.

**Props**:
```typescript
interface ForgotPasswordFormProps {
  onSubmit: (values: ForgotPasswordFormValues) => Promise<void>;
  isSubmitting: boolean;
  isSuccess: boolean;
  resendCountdown: number | null;
}
```

**Success state**: When `isSuccess = true`, replaces form with success message: "Si el email existe, recibirás instrucciones" and button shows resend countdown.

**Dependencies**: `Card`, `Input`, `Button`, `Link`

---

#### 37. `frontend/src/features/auth/components/ResetPasswordForm.tsx`

**Purpose**: New password + confirm form.

**Props**:
```typescript
interface ResetPasswordFormProps {
  onSubmit: (values: ResetPasswordFormValues) => Promise<void>;
  isSubmitting: boolean;
  error: string | null;
  onTyping: () => void;     // called when user types, clears error
}
```

**Dependencies**: `Card`, `Input`, `Button`

---

### Auth feature — Pages

#### 38. `frontend/src/features/auth/pages/LoginPage.tsx`

**Purpose**: Container for LoginForm. Reads query params for error/success messages.

**Behavior**:
1. Reads `?error=session_expired` from URL → shows "Sesión expirada. Iniciá sesión de nuevo."
2. Reads `?success=password_reset` from URL → shows "Contraseña restablecida con éxito. Iniciá sesión."
3. If already authenticated → redirect to `/`
4. Renders `<LoginForm>` inside a centered full-screen layout
5. On successful login without 2FA → call `queryClient.invalidateQueries({ queryKey: ['me'] })`, navigate to redirect target or `/`
6. On `needs2FA` result → navigate to `/2fa` with `state: { preAuthToken }`

**Layout**: Full-screen centered with gradient background (optional), logo at top.

**Dependencies**: `LoginForm`, `useLoginForm()`, `useAuth()`, `useSearchParams`, `useNavigate`

---

#### 39. `frontend/src/features/auth/pages/TwoFactorPage.tsx`

**Purpose**: Container for TwoFactorForm.

**Behavior**:
1. Read `preAuthToken` from navigation state
2. If no `preAuthToken` → redirect to `/login`
3. Renders `<TwoFactorForm>` inside centered layout
4. On success → `queryClient.invalidateQueries({ queryKey: ['me'] })`, navigate to `/`

**Dependencies**: `TwoFactorForm`, `useAuth()`, `useLocation`, `useNavigate`

---

#### 40. `frontend/src/features/auth/pages/ForgotPasswordPage.tsx`

**Purpose**: Container for ForgotPasswordForm.

**Behavior**:
1. Renders `<ForgotPasswordForm>` inside centered layout
2. No special auth check (anonymous can access)

**Dependencies**: `ForgotPasswordForm`, `useForgotPasswordForm()`

---

#### 41. `frontend/src/features/auth/pages/ResetPasswordPage.tsx`

**Purpose**: Container for ResetPasswordForm.

**Behavior**:
1. Read `token` from `useSearchParams()`
2. If no token → navigate to `/forgot-password`
3. Renders `<ResetPasswordForm>` inside centered layout
4. On success → navigate to `/login?success=password_reset`

**Dependencies**: `ResetPasswordForm`, `useResetPasswordForm()`, `useSearchParams`, `useNavigate`

---

### Pages

#### 42. `frontend/src/features/auth/pages/DashboardHome.tsx`

**Purpose**: Landing page after login. Redirects based on user roles.

**Behavior**:
1. Read `user.roles` from `useAuth()`
2. Define redirect priority list: `['/alumnos', '/materias', '/comisiones', '/comunicacion', '/equipos', '/liquidaciones']`
3. Iterate priority list, find first route the user has permission for → `<Navigate to={route} />`
4. If no matching route → render "No tenés acceso a ningún módulo" with logout button (REQ-SHELL-08 scenario 3)

**Dependencies**: `useAuth()`, `usePermissions()`, `Navigate` (react-router-dom)

---

## 7. Tailwind v4 Theme Configuration

### `index.css` — `@theme` block

```css
@import "tailwindcss";

@theme {
  /* Brand color scale — blue */
  --color-primary-50: #eff6ff;
  --color-primary-100: #dbeafe;
  --color-primary-200: #bfdbfe;
  --color-primary-300: #93c5fd;
  --color-primary-400: #60a5fa;
  --color-primary-500: #3b82f6;
  --color-primary-600: #2563eb;
  --color-primary-700: #1d4ed8;
  --color-primary-800: #1e40af;
  --color-primary-900: #1e3a8a;

  /* Semantic colors */
  --color-success-50: #f0fdf4;
  --color-success-100: #dcfce7;
  --color-success-500: #22c55e;
  --color-success-600: #16a34a;

  --color-warning-50: #fffbeb;
  --color-warning-100: #fef3c7;
  --color-warning-500: #f59e0b;
  --color-warning-600: #d97706;

  --color-danger-50: #fef2f2;
  --color-danger-100: #fee2e2;
  --color-danger-500: #ef4444;
  --color-danger-600: #dc2626;

  --color-info-50: #f0f9ff;
  --color-info-100: #e0f2fe;
  --color-info-500: #0ea5e9;
  --color-info-600: #0284c7;

  /* Neutral / gray scale */
  --color-neutral-50: #f8f9fa;
  --color-neutral-100: #f1f3f5;
  --color-neutral-200: #e9ecef;
  --color-neutral-300: #dee2e6;
  --color-neutral-400: #ced4da;
  --color-neutral-500: #adb5bd;
  --color-neutral-600: #868e96;
  --color-neutral-700: #495057;
  --color-neutral-800: #343a40;
  --color-neutral-900: #212529;

  /* Semantic aliases */
  --color-background: #ffffff;
  --color-foreground: var(--color-neutral-900);
  --color-muted: var(--color-neutral-100);
  --color-muted-foreground: var(--color-neutral-600);
  --color-border: var(--color-neutral-200);
  --color-input: var(--color-neutral-300);
  --color-ring: var(--color-primary-500);

  /* Font families */
  --font-sans: 'Inter', ui-sans-serif, system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, monospace;

  /* Animation keyframes */
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  @keyframes fade-in {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
  }
  @keyframes slide-in-left {
    from { transform: translateX(-100%); }
    to { transform: translateX(0); }
  }

  /* Animation utilities */
  --animate-spin: spin 1s linear infinite;
  --animate-fade-in: fade-in 0.2s ease-out;
  --animate-slide-in-left: slide-in-left 0.3s ease-out;
}

@layer base {
  body {
    @apply bg-neutral-50 text-foreground font-sans antialiased;
  }
}
```

### Usage

- Buttons: `bg-primary-600`, `bg-danger-600`, `bg-secondary-100`
- Cards: `bg-background border border-border rounded-lg shadow-sm`
- Links: `text-primary-600 hover:text-primary-700`
- Success alerts: `bg-success-50 text-success-600 border-success-500`
- Error messages: `text-danger-600`
- Disabled: `opacity-50 cursor-not-allowed`

---

## 8. Data Flow Diagrams

### Login Flow

```
User                  LoginPage              AuthProvider            API Server
 │                       │                       │                      │
 │  submit email+pass    │                       │                      │
 │──────────────────────>│                       │                      │
 │                       │  login(email, pass)   │                      │
 │                       │──────────────────────>│                      │
 │                       │                       │  POST /api/auth/login│
 │                       │                       │─────────────────────>│
 │                       │                       │                      │
 │                       │                       │  ┌─ 200: {access_token}   │
 │                       │                       │  │ (no 2FA)         │
 │                       │                       │  │                  │
 │                       │     {needs2FA: false, │  │                  │
 │                       │      accessToken}      │  │                  │
 │                       │<──────────────────────│  │                  │
 │                       │                       │  │                  │
 │                       │  setAccessToken(token)│  │                  │
 │                       │──────────────────────>│  │                  │
 │                       │                       │  │                  │
 │  navigate to /        │                       │  │                  │
 │<──────────────────────│                       │  │                  │
 │                       │                       │  │                  │
 │                       │                       │  │                  │
 │                       │  ┌─ 200: {pre_auth_token}                  │
 │                       │  │ (2FA required)     │                   │
 │                       │  │                    │                   │
 │                       │     {needs2FA: true,  │                   │
 │                       │      preAuthToken}     │                   │
 │                       │<──────────────────────│                   │
 │  navigate to /2fa     │                       │                   │
 │<──────────────────────│                       │                   │
```

### Token Refresh Flow

```
Component               Axios Interceptor          Refresh Endpoint      AuthProvider
 │                           │                          │                    │
 │  api.get('/alumnos')      │                          │                    │
 │──────────────────────────>│                          │                    │
 │                           │                          │                    │
 │             401 Response  │                          │                    │
 │<──────────────────────────│                          │                    │
 │                           │                          │                    │
 │                           │  isRefreshing = false    │                    │
 │                           │  set isRefreshing = true │                    │
 │                           │                          │                    │
 │                           │  POST /api/auth/refresh  │                    │
 │                           │─────────────────────────>│                    │
 │                           │                          │                    │
 │                           │  ┌─ 200: {access_token}  │                    │
 │                           │  │                       │                    │
 │                           │  setAccessToken(token)   │                    │
 │                           │─────────────────────────────────────────────>│
 │                           │                          │                    │
 │  api.get('/alumnos')      │                          │                    │
 │  (with new token)         │                          │                    │
 │──────────────────────────>│                          │                    │
 │                           │                          │                    │
 │             200 Response  │                          │                    │
 │<──────────────────────────│                          │                    │
 │                           │                          │                    │
 │  ┌─ If REFRESH FAILS (401)                          │                    │
 │  │  clearAccessToken()    │                          │                    │
 │  │──────────────────────────────────────────────────>│                    │
 │  │                        │                          │                    │
 │  │  window.location =     │                          │                    │
 │  │  '/login'              │                          │                    │
 │  │─────────────────────────── (hard redirect) ──────>│                    │
```

### Concurrent 401 Queue

```
Comp A              Comp B              Comp C          Axios Interceptor      Refresh
  │                    │                  │                    │                 │
  │──api.get('/a')──>  │                  │                    │                 │
  │       401          │                  │                    │                 │
  │<───────────────────│                  │                    │                 │
  │                    │                  │  isRefreshing=false                 │
  │                    │                  │  set isRefreshing=true              │
  │                    │──api.get('/b')─> │                    │                 │
  │                    │       401        │                    │                 │
  │                    │                  │  isRefreshing=true  │                 │
  │                    │                  │  QUEUE request      │                 │
  │                    │                  │                    │                 │
  │                    │                  │──api.get('/c')────>│                 │
  │                    │                  │       401          │                 │
  │                    │                  │  isRefreshing=true  │                 │
  │                    │                  │  QUEUE request      │                 │
  │                    │                  │                    │                 │
  │                    │                  │                    │ POST /refresh   │
  │                    │                  │                    │────────────────>│
  │                    │                  │                    │                 │
  │                    │                  │                    │ 200: new_token  │
  │                    │                  │                    │<────────────────│
  │                    │                  │                    │                 │
  │                    │                  │  setAccessToken()  │                 │
  │                    │                  │  Process queue:    │                 │
  │                    │                  │  - retry A         │                 │
  │                    │                  │  - retry B         │                 │
  │                    │                  │  - retry C         │                 │
  │                    │                  │  isRefreshing=false│                 │
```

### 2FA Verification Flow

```
User              TwoFactorPage        AuthProvider          API Server
 │                     │                     │                    │
 │  enter 6-digit code │                     │                    │
 │────────────────────>│                     │                    │
 │                     │  verify2FA(token,   │                    │
 │                     │    code)            │                    │
 │                     │────────────────────>│                    │
 │                     │                     │ POST /2fa/verify   │
 │                     │                     │───────────────────>│
 │                     │                     │                    │
 │                     │                     │  ┌─ 200: {access_token}
 │                     │                     │  │                  │
 │                     │    accessToken      │  │                  │
 │                     │<────────────────────│  │                  │
 │                     │                     │  │                  │
 │  navigate to /      │                     │  │                  │
 │<────────────────────│                     │  │                  │
 │                     │                     │  │                  │
 │                     │                     │  ┌─ 401 (expired)   │
 │                     │                     │  │                  │
 │  navigate to /login │                     │  │                  │
 │  "Sesión expirada"  │<────────────────────│  │                  │
 │<────────────────────│                     │  │                  │
 │                     │                     │  ┌─ 400 (bad code)  │
 │                     │   "Código inválido" │  │                  │
 │<────────────────────│─────────────────────│  │                  │
```

---

## 9. API Contracts

### POST /api/auth/login

| Field | Value |
|-------|-------|
| Method | `POST` |
| Path | `/api/auth/login` |
| Auth required | No |
| Rate limited | Yes (429 after 5 req/60s) |

**Request**:
```json
{
  "email": "user@example.com",
  "password": "secret123"
}
```

**Response 200 (no 2FA)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Response 200 (2FA required)**:
```json
{
  "pre_auth_token": "tmp_pre_auth_abc123",
  "token_type": "bearer"
}
```

**Error 401**:
```json
{
  "detail": "Credenciales inválidas"
}
```

**Error 422** (validation):
```json
{
  "detail": [
    { "loc": ["body", "email"], "msg": "field required", "type": "value_error.missing" }
  ]
}
```

**Error 429** (rate limited):
```json
{
  "detail": "Demasiados intentos. Esperá 60 segundos."
}
```
Header: `Retry-After: 45`

---

### POST /api/auth/2fa/verify

| Field | Value |
|-------|-------|
| Method | `POST` |
| Path | `/api/auth/2fa/verify` |
| Auth required | No (uses `pre_auth_token`) |

**Request**:
```json
{
  "pre_auth_token": "tmp_pre_auth_abc123",
  "code": "123456"
}
```

**Response 200**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Error 400** (invalid code):
```json
{
  "detail": "Código inválido"
}
```

**Error 401** (expired pre_auth_token):
```json
{
  "detail": "pre_auth_token expirado"
}
```

---

### POST /api/auth/refresh

| Field | Value |
|-------|-------|
| Method | `POST` |
| Path | `/api/auth/refresh` |
| Auth required | No (uses HttpOnly cookie) |
| Cookie | `refresh_token=...` (HttpOnly, Secure, Path=/api/auth/refresh) |

**Request**: Empty body `{}`

**Response 200**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Error 401** (expired/invalid refresh token):
```json
{
  "detail": "refresh_token inválido o expirado"
}
```

---

### GET /api/auth/me

| Field | Value |
|-------|-------|
| Method | `GET` |
| Path | `/api/auth/me` |
| Auth required | Yes (Bearer token) |

**Response 200**:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "nombre": "Juan",
  "apellido": "Pérez",
  "roles": [
    {
      "id": "role-uuid",
      "name": "admin",
      "permissions": ["alumnos:read", "alumnos:write", "materias:read", ...]
    }
  ],
  "tenant_id": "tenant-uuid",
  "is_impersonating": false
}
```

**Error 401** (missing/expired token):
```json
{
  "detail": "No autorizado"
}
```

---

### POST /api/auth/logout

| Field | Value |
|-------|-------|
| Method | `POST` |
| Path | `/api/auth/logout` |
| Auth required | Yes (Bearer token) |

**Request**: Empty body `{}`

**Response 204**: No content (success)

**Error 401**:
```json
{
  "detail": "No autorizado"
}
```

---

### POST /api/auth/forgot

| Field | Value |
|-------|-------|
| Method | `POST` |
| Path | `/api/auth/forgot` |
| Auth required | No |

**Request**:
```json
{
  "email": "user@example.com"
}
```

**Response 202**: No content (always, regardless of whether email exists — anti-enumeration)

**Error 422** (validation):
```json
{
  "detail": [
    { "loc": ["body", "email"], "msg": "field required", "type": "value_error.missing" }
  ]
}
```

**Error 429** (rate limited): Same structure as login 429

---

### POST /api/auth/reset

| Field | Value |
|-------|-------|
| Method | `POST` |
| Path | `/api/auth/reset` |
| Auth required | No (uses reset token from email) |

**Request**:
```json
{
  "token": "reset_token_abc123",
  "new_password": "newSecurePass42"
}
```

**Response 204**: No content (success)

**Error 400**:
```json
{
  "detail": "Token inválido o expirado"
}
```

**Error 422** (validation):
```json
{
  "detail": [
    { "loc": ["body", "new_password"], "msg": "ensure this value has at least 8 characters", "type": "value_error" }
  ]
}
```

---

### POST /api/auth/impersonation/stop

| Field | Value |
|-------|-------|
| Method | `POST` |
| Path | `/api/auth/impersonation/stop` |
| Auth required | Yes (Bearer token, admin role) |

**Request**: Empty body `{}`

**Response 200**: Returns the original admin's `MeResponse` (full user object)

---

## Implementation Notes

### On the preAuthToken being page-scoped (not in AuthContext)

The `pre_auth_token` is an ephemeral token with a 5-minute TTL. It is stored in React state at the **page level** (`LoginPage` passes it via React Router's `location.state` to `TwoFactorPage`). AuthContext does not store it because:
1. It's only meaningful for the current login flow
2. If the user navigates away from `/2fa` (e.g., browser back), the token is lost and they start over — which is correct behavior
3. It prevents stale tokens from lingering in context

### On the hard redirect vs React navigation after failed refresh

When the refresh fails (line `window.location.href = '/login'`), the code uses a **hard browser navigation** rather than React Router's `navigate()`. This is intentional: the Axios interceptor is outside React's component tree, and a hard redirect ensures all React state is cleared. The AuthProvider will re-mount on the new page and try to refresh again (which will fail, and show the login page).

### On CORS not being needed

Since the frontend is served by Vite (dev) or the same Nginx instance (production), all requests to `/api/*` are same-origin. The Vite proxy in dev and the reverse proxy in production handle forwarding. This means:
- No CORS headers needed from the backend
- `withCredentials: true` works with same-origin semantics
- HttpOnly cookies flow naturally

### On using a separate Axios call for refresh

The refresh endpoint uses `axios.post()` (bare import) instead of `api.post()`. This prevents infinite loops: if the refresh endpoint itself returns 401, the response interceptor would try to refresh the refresh call, ad infinitum. Using a fresh Axios call without interceptors breaks the loop.
