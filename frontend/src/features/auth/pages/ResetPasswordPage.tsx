import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FormProvider } from 'react-hook-form';
import { ResetPasswordForm } from '@/features/auth/components/ResetPasswordForm';
import { useResetPasswordForm } from '@/features/auth/hooks/useResetPassword';

export default function ResetPasswordPage() {
  const navigate = useNavigate();
  const { form, onSubmit, isSubmitting, isSuccess, error, token } = useResetPasswordForm();

  useEffect(() => {
    if (!token) {
      navigate('/forgot-password', { replace: true });
    }
  }, [token, navigate]);

  if (!token) {
    return null;
  }

  if (isSuccess) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50 px-4">
        <p className="text-sm text-success-600">Contraseña restablecida. Redirigiendo...</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-50 px-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-neutral-900">activia · trace</h1>
          <p className="mt-1 text-sm text-muted-foreground">Restablecer contraseña</p>
        </div>

        <FormProvider {...form}>
          <ResetPasswordForm
            onSubmit={onSubmit}
            isSubmitting={isSubmitting}
            error={error}
            onTyping={() => form.clearErrors()}
          />
        </FormProvider>
      </div>
    </div>
  );
}
