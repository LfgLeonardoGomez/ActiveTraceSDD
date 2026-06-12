import { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate, useSearchParams } from 'react-router-dom';
import * as authApi from '@/features/auth/services/auth.api';

const resetSchema = z
  .object({
    new_password: z.string().min(8, 'La contraseña debe tener al menos 8 caracteres'),
    confirm_password: z.string(),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: 'Las contraseñas no coinciden',
    path: ['confirm_password'],
  });

export type ResetPasswordFormValues = z.infer<typeof resetSchema>;

interface UseResetPasswordFormReturn {
  form: ReturnType<typeof useForm<ResetPasswordFormValues>>;
  onSubmit: (e?: React.BaseSyntheticEvent) => Promise<void>;
  isSubmitting: boolean;
  isSuccess: boolean;
  error: string | null;
  token: string | null;
}

export function useResetPasswordForm(): UseResetPasswordFormReturn {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const form = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(resetSchema),
    defaultValues: { new_password: '', confirm_password: '' },
  });

  const onSubmit = useCallback(async () => {
    if (!token) {
      navigate('/forgot-password');
      return;
    }

    const values = form.getValues();
    setIsSubmitting(true);
    setError(null);

    try {
      await authApi.resetPassword({ token, new_password: values.new_password });
      setIsSuccess(true);
      navigate('/login?success=password_reset', { replace: true });
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number } };
      if (axiosErr.response?.status === 400) {
        setError('Token inválido o expirado. Solicitá un nuevo restablecimiento.');
      } else {
        setError('Error al restablecer la contraseña. Intentá de nuevo.');
      }
    } finally {
      setIsSubmitting(false);
    }
  }, [token, form, navigate]);

  return { form, onSubmit, isSubmitting, isSuccess, error, token: token ?? null };
}
