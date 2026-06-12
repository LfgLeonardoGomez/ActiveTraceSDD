import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import type { Carrera, CarreraCreate } from '../../types/estructura.types';

const schema = z.object({
  nombre: z.string().min(1, 'El nombre es obligatorio'),
  codigo: z.string().min(1, 'El código es obligatorio'),
  estado: z.enum(['activo', 'inactivo']).default('activo'),
});

type FormData = z.infer<typeof schema>;

interface CarreraFormProps {
  item?: Carrera | null;
  onSubmit: (data: CarreraCreate) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export default function CarreraForm({ item, onSubmit, onCancel, isLoading }: CarreraFormProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { nombre: '', codigo: '', estado: 'activo' },
  });

  useEffect(() => {
    if (item) {
      reset({ nombre: item.nombre, codigo: item.codigo, estado: item.estado });
    } else {
      reset({ nombre: '', codigo: '', estado: 'activo' });
    }
  }, [item, reset]);

  const handleFormSubmit = (data: FormData) => {
    onSubmit(data as CarreraCreate);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{item ? 'Editar carrera' : 'Nueva carrera'}</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
          <Input label="Nombre" error={errors.nombre?.message} {...register('nombre')} />
          <Input label="Código" error={errors.codigo?.message} {...register('codigo')} />
          <div className="space-y-2">
            <label className="text-sm font-medium">Estado</label>
            <select
              {...register('estado')}
              className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
            >
              <option value="activo">Activo</option>
              <option value="inactivo">Inactivo</option>
            </select>
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
