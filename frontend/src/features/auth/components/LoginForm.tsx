import { Link } from 'react-router-dom';
import { useFormContext } from 'react-hook-form';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/shared/components/ui/Card';
import { Input } from '@/shared/components/ui/Input';
import { Button } from '@/shared/components/ui/Button';
import type { LoginFormValues } from '@/features/auth/hooks/useLogin';

interface LoginFormProps {
  onSubmit: (e?: React.BaseSyntheticEvent) => Promise<void>;
  isSubmitting: boolean;
  error: string | null;
  rateLimitCountdown: number | null;
}

export function LoginForm({ onSubmit, isSubmitting, error, rateLimitCountdown }: LoginFormProps) {
  const { register, formState: { errors } } = useFormContext<LoginFormValues>();

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Iniciar sesión</CardTitle>
        <CardDescription>Ingresá tus credenciales para acceder a trace</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="space-y-4">
          {error && (
            <div className="rounded-md bg-danger-50 p-3 text-sm text-danger-600" role="alert">
              {error}
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

          <Input
            label="Contraseña"
            type="password"
            placeholder="••••••••"
            autoComplete="current-password"
            {...register('password')}
            error={errors.password?.message}
          />

          <Button
            type="submit"
            isLoading={isSubmitting}
            disabled={rateLimitCountdown !== null}
            className="w-full"
          >
            {rateLimitCountdown !== null
              ? `Esperá ${rateLimitCountdown}s`
              : 'Iniciar sesión'}
          </Button>
        </form>
      </CardContent>
      <CardFooter className="justify-center">
        <Link
          to="/forgot-password"
          className="text-sm text-primary-600 hover:text-primary-700 hover:underline"
        >
          ¿Olvidaste tu contraseña?
        </Link>
      </CardFooter>
    </Card>
  );
}
