import { useState, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/shared/services/AuthContext';
import { TwoFactorForm } from '@/features/auth/components/TwoFactorForm';

export default function TwoFactorPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { verify2FA } = useAuth();
  const queryClient = useQueryClient();
  const preAuthToken = (location.state as { preAuthToken?: string })?.preAuthToken;
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!preAuthToken) {
    navigate('/login', { replace: true });
    return null;
  }

  const onSubmit = useCallback(
    async (values: { code: string }) => {
      setIsSubmitting(true);
      setError(null);

      try {
        await verify2FA(preAuthToken, values.code);
        queryClient.invalidateQueries({ queryKey: ['me'] });
        navigate('/', { replace: true });
      } catch (err: unknown) {
        const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
        if (axiosErr.response?.status === 401) {
          navigate('/login?error=session_expired', { replace: true });
        } else if (axiosErr.response?.status === 400) {
          setError(axiosErr.response?.data?.detail ?? 'Código inválido');
        } else {
          setError('Error de verificación. Intentá de nuevo.');
        }
      } finally {
        setIsSubmitting(false);
      }
    },
    [preAuthToken, verify2FA, queryClient, navigate],
  );

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-50 px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-neutral-900">activia · trace</h1>
          <p className="mt-1 text-sm text-muted-foreground">Verificación en dos pasos</p>
        </div>

        <TwoFactorForm
          onSubmit={onSubmit}
          isSubmitting={isSubmitting}
          error={error}
        />
      </div>
    </div>
  );
}
