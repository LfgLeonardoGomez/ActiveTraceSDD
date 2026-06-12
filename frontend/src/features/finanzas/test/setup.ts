import '@testing-library/jest-dom/vitest';
import { vi } from 'vitest';

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useParams: () => ({}),
    useLocation: () => ({ pathname: '/finanzas', search: '', hash: '', state: null, key: '' }),
  };
});

vi.mock('@/shared/services/AuthContext', () => ({
  useAuth: () => ({
    user: { roles: [{ name: 'FINANZAS' }] },
    isAuthenticated: true,
    accessToken: 'mock-token',
    isLoading: false,
    login: vi.fn(),
    verify2FA: vi.fn(),
    logout: vi.fn(),
  }),
}));

vi.mock('@/shared/hooks/usePermissions', () => ({
  usePermissions: () => ({ can: () => true }),
}));

vi.mock('@/shared/services/api', () => ({
  getAccessToken: () => 'mock-token',
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
    interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } },
  },
  setAccessToken: vi.fn(),
  clearAccessToken: vi.fn(),
}));
