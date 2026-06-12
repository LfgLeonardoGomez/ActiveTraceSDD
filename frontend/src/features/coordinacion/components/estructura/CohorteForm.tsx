import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { useCrearCohorte, useActualizarCohorte } from '../../hooks/useEstructura';
import type { Cohorte } from '../../types/estructura.types';

const schema = z.object({
  nombre: z.string().min(1, 'Nombre requerido'),
  year: z.coerce.number({ invalid_type_error: 'Año requerido' }).int().min(2000, 'Año inválido').max(2100, 'Año inválido'),
  fecha_desde: z.string().min(1, 'Fecha de inicio requerida'),
  fecha_hasta: z.string().min(1, 'Fecha de fin requerida'),
  estado: z.string().min(1, 'Estado requerido'),
});

type FormValues = z.infer<typeof schema>;

interface CohorteFormProps {
  cohorte?: Cohorte | null;
  onSuccess?: () => void;
}

export function CohorteForm({ cohorte, onSuccess }: CohorteFormProps) {
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const crearMutation = useCrearCohorte();
  const actualizarMutation = useActualizarCohorte();
  const isEdit = !!cohorte;

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { nombre: '', year: new Date().getFullYear(), fecha_desde: '', fecha_hasta: '', estado: 'activo' },
  });

  useEffect(() => {
    if (cohorte) {
      reset({
        nombre: cohorte.nombre,
        year: cohorte.year,
        fecha_desde: cohorte.fecha_desde,
        fecha_hasta: cohorte.fecha_hasta,
        estado: cohorte.estado,
      });
    }
  }, [cohorte, reset]);

  const onSubmit = async (values: FormValues) => {
    setMessage(null);
    try {
      if (isEdit && cohorte) {
        await actualizarMutation.mutateAsync({ id: cohorte.id, data: values });
        setMessage({ type: 'success', text: 'Cohorte actualizado correctamente' });
      } else {
        await crearMutation.mutateAsync(values);
        setMessage({ type: 'success', text: 'Cohorte creado correctamente' });
      }
      onSuccess?.();
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 409) {
        setMessage({ type: 'error', text: 'Ya existe un cohorte con ese nombre para el año indicado' });
      } else {
        setMessage({ type: 'error', text: `Error al ${isEdit ? 'actualizar' : 'crear'} el cohorte` });
      }
    }
  };

  const isPending = crearMutation.isPending || actualizarMutation.isPending;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{isEdit ? 'Editar Cohorte' : 'Nuevo Cohorte'}</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Nombre"
            placeholder="Ej: 1° Cuatrimestre"
            {...register('nombre')}
            error={errors.nombre?.message}
          />
          <Input
            label="Año"
            type="number"
            {...register('year')}
            error={errors.year?.message}
          />
          <Input
            label="Fecha de inicio"
            type="date"
            {...register('fecha_desde')}
            error={errors.fecha_desde?.message}
          />
          <Input
            label="Fecha de fin"
            type="date"
            {...register('fecha_hasta')}
            error={errors.fecha_hasta?.message}
          />
          <div className="space-y-2">
            <label className="text-sm font-medium text-neutral-700">Estado</label>
            <select
              {...register('estado')}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              <option value="activo">Activo</option>
              <option value="inactivo">Inactivo</option>
            </select>
            {errors.estado && <p className="text-sm text-danger-600">{errors.estado.message}</p>}
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
              : isEdit ? 'Actualizar cohorte' : 'Crear cohorte'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
