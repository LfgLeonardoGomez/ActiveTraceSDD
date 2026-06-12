import { FormProvider } from 'react-hook-form';
import { ForgotPasswordForm } from '@/features/auth/components/ForgotPasswordForm';
import { useForgotPasswordForm } from '@/features/auth/hooks/useForgotPassword';

export default function ForgotPasswordPage() {
  const { form, onSubmit, isSubmitting, isSuccess, resendCountdown, error } =
    useForgotPasswordForm();

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-50 px-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-neutral-900">activia · trace</h1>
          <p className="mt-1 text-sm text-muted-foreground">Recuperación de contraseña</p>
        </div>

        <FormProvider {...form}>
          <ForgotPasswordForm
            onSubmit={onSubmit}
            isSubmitting={isSubmitting}
            isSuccess={isSuccess}
            resendCountdown={resendCountdown}
          />
        </FormProvider>
      </div>
    </div>
  );
}
