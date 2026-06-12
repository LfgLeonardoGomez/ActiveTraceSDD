import { useFormContext } from 'react-hook-form';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/shared/components/ui/Card';
import { Input } from '@/shared/components/ui/Input';
import { Button } from '@/shared/components/ui/Button';
import type { ResetPasswordFormValues } from '@/features/auth/hooks/useResetPassword';

interface ResetPasswordFormProps {
  onSubmit: (e?: React.BaseSyntheticEvent) => Promise<void>;
  isSubmitting: boolean;
  error: string | null;
  onTyping: () => void;
}

export function ResetPasswordForm({
  onSubmit,
  isSubmitting,
  error,
  onTyping,
}: ResetPasswordFormProps) {
  const { register, formState: { errors } } = useFormContext<ResetPasswordFormValues>();

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Restablecer contraseña</CardTitle>
        <CardDescription>Ingresá tu nueva contraseña</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="space-y-4">
          {error && (
            <div className="rounded-md bg-danger-50 p-3 text-sm text-danger-600" role="alert">
              {error}
            </div>
          )}

          <Input
            label="Nueva contraseña"
            type="password"
            placeholder="Mínimo 8 caracteres"
            autoComplete="new-password"
            autoFocus
            {...register('new_password')}
            onChange={(e) => {
              register('new_password').onChange(e);
              onTyping();
            }}
            error={errors.new_password?.message}
          />

          <Input
            label="Confirmar contraseña"
            type="password"
            placeholder="Repetí la contraseña"
            autoComplete="new-password"
            {...register('confirm_password')}
            onChange={(e) => {
              register('confirm_password').onChange(e);
              onTyping();
            }}
            error={errors.confirm_password?.message}
          />

          <Button type="submit" isLoading={isSubmitting} className="w-full">
            Restablecer contraseña
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
