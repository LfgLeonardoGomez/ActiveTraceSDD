export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token?: string;
  pre_auth_token?: string;
  token_type?: string;
}

export interface TwoFactorVerifyRequest {
  pre_auth_token: string;
  code: string;
}

export interface TwoFactorVerifyResponse {
  access_token: string;
  token_type: string;
}

export interface MeResponse {
  id: string;
  email: string;
  nombre: string;
  apellido: string;
  roles: Role[];
  tenant_id: string;
  is_impersonating: boolean;
}

export interface Role {
  id: string;
  name: string;
  permissions: string[];
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

export interface RefreshResponse {
  access_token: string;
  token_type: string;
}

export type LoginResult =
  | { needs2FA: true; preAuthToken: string }
  | { needs2FA: false; accessToken: string };
