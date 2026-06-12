import { useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { FormProvider } from 'react-hook-form';
import { useAuth } from '@/shared/services/AuthContext';
import { LoginForm } from '@/features/auth/components/LoginForm';
import { useLoginForm } from '@/features/auth/hooks/useLogin';
import { Spinner } from '@/shared/components/ui/Spinner';

export default function LoginPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { form, onSubmit, isSubmitting, rateLimitCountdown, error } = useLoginForm();
  const errorParam = searchParams.get('error');
  const successParam = searchParams.get('success');

  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, authLoading, navigate]);

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  const displayError =
    error ??
    (errorParam === 'session_expired' ? 'Sesión expirada. Iniciá sesión de nuevo.' : null);

  const displaySuccess =
    successParam === 'password_reset'
      ? 'Contraseña restablecida con éxito. Iniciá sesión.'
      : null;

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-50 px-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-neutral-900">activia · trace</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Plataforma de gestión académica
          </p>
        </div>

        {displaySuccess && (
          <div className="rounded-md bg-success-50 p-3 text-sm text-success-600 text-center" role="status">
            {displaySuccess}
          </div>
        )}

        <FormProvider {...form}>
          <LoginForm
            onSubmit={onSubmit}
            isSubmitting={isSubmitting}
            error={displayError}
            rateLimitCountdown={rateLimitCountdown}
          />
        </FormProvider>
      </div>
    </div>
  );
}
