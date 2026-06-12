import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import type { Cohorte, CohorteCreate } from '../../types/estructura.types';

const schema = z.object({
  nombre: z.string().min(1, 'El nombre es obligatorio'),
  anio: z.coerce.number().int().positive('El año debe ser positivo'),
  vigencia_desde: z.string().min(1, 'La fecha de inicio es obligatoria'),
  vigencia_hasta: z.string().min(1, 'La fecha de fin es obligatoria'),
  estado: z.enum(['activo', 'inactivo']).default('activo'),
  carrera_id: z.string().uuid('Selecciona una carrera'),
}).refine((data) => data.vigencia_hasta >= data.vigencia_desde, {
  message: 'La fecha de fin debe ser posterior o igual a la de inicio',
  path: ['vigencia_hasta'],
});

type FormData = z.infer<typeof schema>;

interface CohorteFormProps {
  item?: Cohorte | null;
  carreras: { id: string; nombre: string }[];
  onSubmit: (data: CohorteCreate) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export default function CohorteForm({ item, carreras, onSubmit, onCancel, isLoading }: CohorteFormProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      nombre: '',
      anio: new Date().getFullYear(),
      vigencia_desde: '',
      vigencia_hasta: '',
      estado: 'activo',
      carrera_id: '',
    },
  });

  useEffect(() => {
    if (item) {
      reset({
        nombre: item.nombre,
        anio: item.anio,
        vigencia_desde: item.vigencia_desde,
        vigencia_hasta: item.vigencia_hasta,
        estado: item.estado,
        carrera_id: item.carrera_id,
      });
    } else {
      reset({
        nombre: '',
        anio: new Date().getFullYear(),
        vigencia_desde: '',
        vigencia_hasta: '',
        estado: 'activo',
        carrera_id: '',
      });
    }
  }, [item, reset]);

  const handleFormSubmit = (data: FormData) => {
    onSubmit(data as CohorteCreate);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{item ? 'Editar cohorte' : 'Nueva cohorte'}</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
          <Input label="Nombre" error={errors.nombre?.message} {...register('nombre')} />
          <Input label="Año" type="number" error={errors.anio?.message} {...register('anio')} />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Vigencia desde" type="date" error={errors.vigencia_desde?.message} {...register('vigencia_desde')} />
            <Input label="Vigencia hasta" type="date" error={errors.vigencia_hasta?.message} {...register('vigencia_hasta')} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Carrera</label>
            <select
              {...register('carrera_id')}
              className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
            >
              <option value="">Seleccionar...</option>
              {carreras.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nombre}
                </option>
              ))}
            </select>
            {errors.carrera_id && (
              <p className="text-sm text-danger-600" role="alert">
                {errors.carrera_id.message}
              </p>
            )}
          </div>
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
