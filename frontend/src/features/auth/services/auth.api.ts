import api, { getAccessToken } from '@/shared/services/api';
import axios from 'axios';
import type {
  LoginRequest,
  LoginResponse,
  TwoFactorVerifyRequest,
  TwoFactorVerifyResponse,
  ForgotPasswordRequest,
  ResetPasswordRequest,
  RefreshResponse,
} from '@/features/auth/types/auth.types';

function baseURL(): string {
  return import.meta.env.VITE_API_BASE_URL ?? '';
}

export async function login(data: LoginRequest): Promise<LoginResponse> {
  const { data: response } = await axios.post<LoginResponse>(
    `${baseURL()}/api/auth/login`,
    data,
    { headers: { 'Content-Type': 'application/json' } },
  );
  return response;
}

export async function verify2FA(data: TwoFactorVerifyRequest): Promise<TwoFactorVerifyResponse> {
  const { data: response } = await axios.post<TwoFactorVerifyResponse>(
    `${baseURL()}/api/auth/2fa/verify`,
    data,
    { headers: { 'Content-Type': 'application/json' } },
  );
  return response;
}

export async function logout(): Promise<void> {
  await api.post('/api/auth/logout');
}

export async function forgotPassword(data: ForgotPasswordRequest): Promise<void> {
  await axios.post(`${baseURL()}/api/auth/forgot`, data, {
    headers: { 'Content-Type': 'application/json' },
  });
}

export async function resetPassword(data: ResetPasswordRequest): Promise<void> {
  await axios.post(`${baseURL()}/api/auth/reset`, data, {
    headers: { 'Content-Type': 'application/json' },
  });
}

export async function refresh(): Promise<RefreshResponse> {
  const { data } = await axios.post<RefreshResponse>(
    `${baseURL()}/api/auth/refresh`,
    {},
    { withCredentials: true },
  );
  return data;
}
