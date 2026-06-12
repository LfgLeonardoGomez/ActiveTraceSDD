import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import api, { setAccessToken, getAccessToken, clearAccessToken } from './api';
import type { MeResponse, LoginResult, TwoFactorVerifyResponse } from '@/features/auth/types/auth.types';
import axios from 'axios';

// ── Types ──
interface AuthState {
  user: MeResponse | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<LoginResult>;
  verify2FA: (preAuthToken: string, code: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

// ── Hook ──
export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// ── Base URL helper ──
function baseURL(): string {
  return import.meta.env.VITE_API_BASE_URL ?? '';
}

// ── /me query hook (internal) ──
function useMeQuery() {
  return useQuery<MeResponse>({
    queryKey: ['me'],
    queryFn: async () => {
      const { data } = await api.get<MeResponse>('/api/auth/me');
      return data;
    },
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    retry: 1,
    enabled: !!getAccessToken(),
  });
}

// ── Provider ──
export function AuthProvider({ children }: { children: ReactNode }) {
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const queryClient = useQueryClient();
  const { data: user, refetch: refetchMe } = useMeQuery();

  // ── On mount: try to refresh the token ──
  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      try {
        const { data } = await axios.post<{ access_token: string }>(
          `${baseURL()}/api/auth/refresh`,
          {},
          { withCredentials: true },
        );
        if (cancelled) return;

        setAccessToken(data.access_token);
        setIsAuthenticated(true);
        // refetchMe will be triggered by the enabled flag changing
        await refetchMe();
      } catch {
        if (cancelled) return;
        setIsAuthenticated(false);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    bootstrap();

    return () => {
      cancelled = true;
    };
    // Run once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Sync isAuthenticated with user presence ──
  useEffect(() => {
    if (!isLoading) {
      setIsAuthenticated(!!user);
    }
  }, [user, isLoading]);

  // ── login ──
  const login = useCallback(async (email: string, password: string): Promise<LoginResult> => {
    const response = await axios.post<{ access_token?: string; pre_auth_token?: string }>(
      `${baseURL()}/api/auth/login`,
      { email, password },
      { headers: { 'Content-Type': 'application/json' } },
    );

    if (response.data.access_token) {
      // No 2FA required
      setAccessToken(response.data.access_token);
      setIsAuthenticated(true);
      queryClient.invalidateQueries({ queryKey: ['me'] });
      return { needs2FA: false, accessToken: response.data.access_token };
    }

    if (response.data.pre_auth_token) {
      // 2FA required
      return { needs2FA: true, preAuthToken: response.data.pre_auth_token };
    }

    throw new Error('Respuesta inesperada del servidor');
  }, [queryClient]);

  // ── verify2FA ──
  const verify2FA = useCallback(async (preAuthToken: string, code: string): Promise<void> => {
    const response = await axios.post<TwoFactorVerifyResponse>(
      `${baseURL()}/api/auth/2fa/verify`,
      { pre_auth_token: preAuthToken, code },
      { headers: { 'Content-Type': 'application/json' } },
    );

    setAccessToken(response.data.access_token);
    setIsAuthenticated(true);
    queryClient.invalidateQueries({ queryKey: ['me'] });
  }, [queryClient]);

  // ── logout ──
  const logout = useCallback(async (): Promise<void> => {
    try {
      await api.post('/api/auth/logout');
    } catch {
      // Always clear state regardless of response
    } finally {
      clearAccessToken();
      setIsAuthenticated(false);
      queryClient.clear();
    }
  }, [queryClient]);

  const value: AuthState = {
    user: user ?? null,
    accessToken: getAccessToken(),
    isAuthenticated,
    isLoading,
    login,
    verify2FA,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
