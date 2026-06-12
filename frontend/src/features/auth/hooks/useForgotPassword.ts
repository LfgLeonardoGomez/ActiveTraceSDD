import { useState, useCallback, useEffect, useRef } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import * as authApi from '@/features/auth/services/auth.api';

const forgotSchema = z.object({
  email: z.string().email('Email inválido'),
});

export type ForgotPasswordFormValues = z.infer<typeof forgotSchema>;

interface UseForgotPasswordFormReturn {
  form: ReturnType<typeof useForm<ForgotPasswordFormValues>>;
  onSubmit: (e?: React.BaseSyntheticEvent) => Promise<void>;
  isSubmitting: boolean;
  isSuccess: boolean;
  resendCountdown: number | null;
  error: string | null;
}

export function useForgotPasswordForm(): UseForgotPasswordFormReturn {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [resendCountdown, setResendCountdown] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const form = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(forgotSchema),
    defaultValues: { email: '' },
  });

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
      await authApi.forgotPassword(values);
      setIsSuccess(true);
      setResendCountdown(30);

      intervalRef.current = setInterval(() => {
        setResendCountdown((prev) => {
          if (prev === null || prev <= 1) {
            if (intervalRef.current) clearInterval(intervalRef.current);
            return null;
          }
          return prev - 1;
        });
      }, 1000);
    } catch {
      setError('Error al enviar la solicitud. Intentá de nuevo.');
    } finally {
      setIsSubmitting(false);
    }
  }, [form]);

  return { form, onSubmit, isSubmitting, isSuccess, resendCountdown, error };
}
