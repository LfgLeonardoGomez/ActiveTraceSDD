import { useState, useCallback, useEffect, useRef } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '@/shared/services/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';

const loginSchema = z.object({
  email: z.string().email('Email inválido'),
  password: z.string().min(8, 'La contraseña debe tener al menos 8 caracteres'),
});

export type LoginFormValues = z.infer<typeof loginSchema>;

interface UseLoginFormReturn {
  form: ReturnType<typeof useForm<LoginFormValues>>;
  onSubmit: (e?: React.BaseSyntheticEvent) => Promise<void>;
  isSubmitting: boolean;
  rateLimitCountdown: number | null;
  error: string | null;
  clearError: () => void;
}

export function useLoginForm(): UseLoginFormReturn {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [rateLimitCountdown, setRateLimitCountdown] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  });

  const clearError = useCallback(() => setError(null), []);

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const onSubmit = useCallback(async () => {
    const values = form.getValues();
    setIsSubmitting(true);
    setError(null);

    try {
      const result = await login(values.email, values.password);

      if (result.needs2FA) {
        navigate('/2fa', { state: { preAuthToken: result.preAuthToken } });
      } else {
        const from = (location.state as { from?: string })?.from ?? '/';
        navigate(from, { replace: true });
      }
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
        if (axiosErr.response?.status === 401) {
          setError('Credenciales inválidas');
          form.setValue('password', '');
        } else if (axiosErr.response?.status === 429) {
          const retryAfter = parseInt(
            (err as { response?: { headers?: Record<string, string> } }).response?.headers?.['retry-after'] ?? '60',
            10,
          );
          setRateLimitCountdown(retryAfter);
          setError(`Demasiados intentos. Esperá ${retryAfter} segundos.`);

          intervalRef.current = setInterval(() => {
            setRateLimitCountdown((prev) => {
              if (prev === null || prev <= 1) {
                if (intervalRef.current) clearInterval(intervalRef.current);
                return null;
              }
              return prev - 1;
            });
          }, 1000);
        } else {
          setError('Error de conexión. Intentá de nuevo.');
        }
      } else {
        setError('Error de conexión. Intentá de nuevo.');
      }
    } finally {
      setIsSubmitting(false);
    }
  }, [form, login, navigate, location.state]);

  return { form, onSubmit, isSubmitting, rateLimitCountdown, error, clearError };
}
