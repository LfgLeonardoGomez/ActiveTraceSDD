import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/shared/components/ui/Card';
import { Input } from '@/shared/components/ui/Input';
import { Button } from '@/shared/components/ui/Button';

const twoFactorSchema = z.object({
  code: z
    .string()
    .length(6, 'El código debe tener 6 dígitos')
    .regex(/^\d+$/, 'El código debe ser numérico'),
});

type TwoFactorFormValues = z.infer<typeof twoFactorSchema>;

interface TwoFactorFormProps {
  onSubmit: (values: TwoFactorFormValues) => Promise<void>;
  isSubmitting: boolean;
  error: string | null;
}

export function TwoFactorForm({ onSubmit, isSubmitting, error }: TwoFactorFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<TwoFactorFormValues>({
    resolver: zodResolver(twoFactorSchema),
  });

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle>Verificación en dos pasos</CardTitle>
        <CardDescription>
          Ingresá el código de 6 dígitos de tu aplicación autenticadora
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {error && (
            <div className="rounded-md bg-danger-50 p-3 text-sm text-danger-600" role="alert">
              {error}
            </div>
          )}

          <Input
            label="Código de verificación"
            placeholder="123456"
            maxLength={6}
            inputMode="numeric"
            pattern="[0-9]*"
            autoComplete="one-time-code"
            autoFocus
            {...register('code')}
            error={errors.code?.message}
          />

          <Button type="submit" isLoading={isSubmitting} className="w-full">
            Verificar
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
