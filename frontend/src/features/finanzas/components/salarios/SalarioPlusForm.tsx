import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import type { SalarioPlus, SalarioPlusCreate } from '../../types/salarios.types';

const schema = z.object({
  grupo: z.string().min(1, 'El grupo es obligatorio'),
  rol: z.string().min(1, 'El rol es obligatorio'),
  monto: z.coerce.number().positive('El monto debe ser positivo'),
  vigencia_desde: z.string().min(1, 'La fecha de inicio es obligatoria'),
  vigencia_hasta: z.string().min(1, 'La fecha de fin es obligatoria'),
}).refine((data) => data.vigencia_hasta >= data.vigencia_desde, {
  message: 'La fecha de fin debe ser posterior o igual a la de inicio',
  path: ['vigencia_hasta'],
});

type FormData = z.infer<typeof schema>;

interface SalarioPlusFormProps {
  item?: SalarioPlus | null;
  onSubmit: (data: SalarioPlusCreate) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export default function SalarioPlusForm({ item, onSubmit, onCancel, isLoading }: SalarioPlusFormProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      grupo: '',
      rol: '',
      monto: 0,
      vigencia_desde: '',
      vigencia_hasta: '',
    },
  });

  useEffect(() => {
    if (item) {
      reset({
        grupo: item.grupo,
        rol: item.rol,
        monto: item.monto,
        vigencia_desde: item.vigencia_desde,
        vigencia_hasta: item.vigencia_hasta,
      });
    } else {
      reset({ grupo: '', rol: '', monto: 0, vigencia_desde: '', vigencia_hasta: '' });
    }
  }, [item, reset]);

  const handleFormSubmit = (data: FormData) => {
    onSubmit(data as SalarioPlusCreate);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{item ? 'Editar salario plus' : 'Nuevo salario plus'}</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
          <Input
            label="Grupo"
            placeholder="Ej: Grupo A"
            error={errors.grupo?.message}
            {...register('grupo')}
          />
          <Input
            label="Rol"
            placeholder="Ej: TUTOR, PROFESOR..."
            error={errors.rol?.message}
            {...register('rol')}
          />
          <Input
            label="Monto"
            type="number"
            step="0.01"
            error={errors.monto?.message}
            {...register('monto')}
          />
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Vigencia desde"
              type="date"
              error={errors.vigencia_desde?.message}
              {...register('vigencia_desde')}
            />
            <Input
              label="Vigencia hasta"
              type="date"
              error={errors.vigencia_hasta?.message}
              {...register('vigencia_hasta')}
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>
              Cancelar
            </Button>
            <Button type="submit" isLoading={isLoading}>
              {item ? 'Guardar cambios' : 'Crear'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
