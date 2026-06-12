import { useFormContext } from 'react-hook-form';
import { Link } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/shared/components/ui/Card';
import { Input } from '@/shared/components/ui/Input';
import { Button } from '@/shared/components/ui/Button';
import type { ForgotPasswordFormValues } from '@/features/auth/hooks/useForgotPassword';

interface ForgotPasswordFormProps {
  onSubmit: (e?: React.BaseSyntheticEvent) => Promise<void>;
  isSubmitting: boolean;
  isSuccess: boolean;
  resendCountdown: number | null;
}

export function ForgotPasswordForm({
  onSubmit,
  isSubmitting,
  isSuccess,
  resendCountdown,
}: ForgotPasswordFormProps) {
  const { register, formState: { errors } } = useFormContext<ForgotPasswordFormValues>();

  if (isSuccess) {
    return (
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Revisá tu email</CardTitle>
          <CardDescription>
            Si el email existe, vas a recibir instrucciones para restablecer tu contraseña.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-md bg-success-50 p-3 text-sm text-success-600">
            Email enviado. Revisá tu bandeja de entrada.
          </div>
          <Button
            type="button"
            variant="outline"
            className="w-full"
            disabled={resendCountdown !== null}
            onClick={onSubmit}
            isLoading={isSubmitting}
          >
            {resendCountdown !== null
              ? `Reenviar en ${resendCountdown}s`
              : 'Reenviar email'}
          </Button>
        </CardContent>
        <CardFooter className="justify-center">
          <Link
            to="/login"
            className="text-sm text-primary-600 hover:text-primary-700 hover:underline"
          >
            Volver a iniciar sesión
          </Link>
        </CardFooter>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Recuperar contraseña</CardTitle>
        <CardDescription>
          Te enviaremos un enlace para restablecer tu contraseña
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="space-y-4">
          {errors.email?.message && (
            <div className="rounded-md bg-danger-50 p-3 text-sm text-danger-600" role="alert">
              {errors.email.message}
            </div>
          )}

          <Input
            label="Email"
            type="email"
            placeholder="tu@email.com"
            autoComplete="email"
            autoFocus
            {...register('email')}
            error={errors.email?.message}
          />

          <Button type="submit" isLoading={isSubmitting} className="w-full">
            Enviar instrucciones
          </Button>
        </form>
      </CardContent>
      <CardFooter className="justify-center">
        <Link
          to="/login"
          className="text-sm text-primary-600 hover:text-primary-700 hover:underline"
        >
          Volver a iniciar sesión
        </Link>
      </CardFooter>
    </Card>
  );
}
