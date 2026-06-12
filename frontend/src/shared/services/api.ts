import axios from 'axios';

// ── In-memory token store (module-level closure) ──
let accessToken: string | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

export function clearAccessToken(): void {
  accessToken = null;
}

// ── Axios instance ──
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});

// ── Request interceptor: attach Bearer token ──
api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

// ── Response interceptor: transparent token refresh ──
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
      // NOTE: using bare axios.post() — NOT the api instance — to avoid interceptor loops
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
      // Hard redirect — clears all React state
      window.location.href = '/login';

      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  },
);

export default api;
