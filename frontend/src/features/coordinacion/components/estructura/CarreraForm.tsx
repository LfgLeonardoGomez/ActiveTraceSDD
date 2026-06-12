import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { useCrearCarrera, useActualizarCarrera } from '../../hooks/useEstructura';
import type { Carrera } from '../../types/estructura.types';

const schema = z.object({
  codigo: z.string().min(1, 'Código requerido'),
  nombre: z.string().min(1, 'Nombre requerido'),
  activa: z.boolean(),
});

type FormValues = z.infer<typeof schema>;

interface CarreraFormProps {
  carrera?: Carrera | null;
  onSuccess?: () => void;
}

export function CarreraForm({ carrera, onSuccess }: CarreraFormProps) {
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const crearMutation = useCrearCarrera();
  const actualizarMutation = useActualizarCarrera();
  const isEdit = !!carrera;

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { codigo: '', nombre: '', activa: true },
  });

  useEffect(() => {
    if (carrera) {
      reset({ codigo: carrera.codigo, nombre: carrera.nombre, activa: carrera.activa });
    }
  }, [carrera, reset]);

  const onSubmit = async (values: FormValues) => {
    setMessage(null);
    try {
      if (isEdit && carrera) {
        await actualizarMutation.mutateAsync({ id: carrera.id, data: values });
        setMessage({ type: 'success', text: 'Carrera actualizada correctamente' });
      } else {
        await crearMutation.mutateAsync(values);
        setMessage({ type: 'success', text: 'Carrera creada correctamente' });
      }
      onSuccess?.();
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 409) {
        setMessage({ type: 'error', text: 'El código ya está registrado' });
      } else {
        setMessage({ type: 'error', text: `Error al ${isEdit ? 'actualizar' : 'crear'} la carrera` });
      }
    }
  };

  const isPending = crearMutation.isPending || actualizarMutation.isPending;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{isEdit ? 'Editar Carrera' : 'Nueva Carrera'}</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Código"
            placeholder="Ej: LIC-MAT"
            {...register('codigo')}
            error={errors.codigo?.message}
          />
          <Input
            label="Nombre"
            placeholder="Ej: Licenciatura en Matemática"
            {...register('nombre')}
            error={errors.nombre?.message}
          />
          <div className="flex items-center gap-2">
            <input type="checkbox" id="activa" {...register('activa')} className="rounded border-neutral-300" />
            <label htmlFor="activa" className="text-sm font-medium text-neutral-700">Activa</label>
          </div>

          {message && (
            <div
              className={`rounded-md p-3 text-sm ${
                message.type === 'success' ? 'bg-success-50 text-success-600' : 'bg-danger-50 text-danger-600'
              }`}
            >
              {message.text}
            </div>
          )}

          <Button type="submit" isLoading={isPending} disabled={isPending}>
            {isPending
              ? isEdit ? 'Actualizando...' : 'Creando...'
              : isEdit ? 'Actualizar carrera' : 'Crear carrera'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
