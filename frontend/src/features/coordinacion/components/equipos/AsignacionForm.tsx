import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { useCrearAsignacion } from '../../hooks/useEquipos';

const schema = z.object({
  docente_id: z.string().min(1, 'Docente requerido'),
  materia_id: z.string().min(1, 'Materia requerida'),
  carrera_id: z.string().min(1, 'Carrera requerida'),
  cohorte_id: z.string().min(1, 'Cohorte requerida'),
  rol: z.string().min(1, 'Rol requerido'),
  fecha_desde: z.string().min(1, 'Fecha desde requerida'),
  fecha_hasta: z.string().min(1, 'Fecha hasta requerida'),
}).refine((data) => !data.fecha_desde || !data.fecha_hasta || data.fecha_hasta > data.fecha_desde, {
  message: 'La fecha hasta debe ser posterior a la fecha desde',
  path: ['fecha_hasta'],
});

type FormValues = z.infer<typeof schema>;

interface AsignacionFormProps {
  onSuccess?: () => void;
}

export function AsignacionForm({ onSuccess }: AsignacionFormProps) {
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const mutation = useCrearAsignacion();

  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (values: FormValues) => {
    setMessage(null);
    try {
      await mutation.mutateAsync(values);
      setMessage({ type: 'success', text: 'Asignación creada correctamente' });
      onSuccess?.();
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 409) {
        setMessage({ type: 'error', text: 'El docente ya está asignado' });
      } else {
        setMessage({ type: 'error', text: 'Error al crear la asignación' });
      }
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Nueva Asignación</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Docente ID"
            {...register('docente_id')}
            error={errors.docente_id?.message}
            placeholder="Buscar docente (mín. 3 caracteres)"
          />
          <Input
            label="Materia ID"
            {...register('materia_id')}
            error={errors.materia_id?.message}
          />
          <Input
            label="Carrera ID"
            {...register('carrera_id')}
            error={errors.carrera_id?.message}
          />
          <Input
            label="Cohorte ID"
            {...register('cohorte_id')}
            error={errors.cohorte_id?.message}
          />
          <Input
            label="Rol"
            {...register('rol')}
            error={errors.rol?.message}
            placeholder="PROFESOR / TUTOR / NEXO / COORDINADOR"
          />
          <Input
            label="Fecha desde"
            type="date"
            {...register('fecha_desde')}
            error={errors.fecha_desde?.message}
          />
          <Input
            label="Fecha hasta"
            type="date"
            {...register('fecha_hasta')}
            error={errors.fecha_hasta?.message}
          />

          {message && (
            <div
              className={`rounded-md p-3 text-sm ${
                message.type === 'success'
                  ? 'bg-success-50 text-success-600'
                  : 'bg-danger-50 text-danger-600'
              }`}
            >
              {message.text}
            </div>
          )}

          <Button type="submit" isLoading={mutation.isPending} disabled={mutation.isPending}>
            {mutation.isPending ? 'Creando...' : 'Crear asignación'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
