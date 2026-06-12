import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { useCrearEvaluacion, useActualizarEvaluacion } from '../../hooks/useEstructura';
import type { Evaluacion } from '../../types/estructura.types';

const schema = z.object({
  materia: z.string().min(1, 'Materia requerida'),
  cohorte: z.string().min(1, 'Cohorte requerido'),
  tipo: z.enum(['parcial', 'tp', 'coloquio'], { errorMap: () => ({ message: 'Tipo inválido' }) }),
  instancia: z.coerce.number({ invalid_type_error: 'Instancia requerida' }).int().min(1, 'Mínimo 1'),
  fecha: z.string().min(1, 'Fecha requerida'),
  titulo: z.string().min(1, 'Título requerido'),
});

type FormValues = z.infer<typeof schema>;

const TIPOS = [
  { value: 'parcial', label: 'Parcial' },
  { value: 'tp', label: 'TP' },
  { value: 'coloquio', label: 'Coloquio' },
] as const;

interface EvaluacionFormProps {
  evaluacion?: Evaluacion | null;
  onSuccess?: () => void;
}

export function EvaluacionForm({ evaluacion, onSuccess }: EvaluacionFormProps) {
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [pastDateWarning, setPastDateWarning] = useState(false);
  const crearMutation = useCrearEvaluacion();
  const actualizarMutation = useActualizarEvaluacion();
  const isEdit = !!evaluacion;

  const { register, handleSubmit, reset, watch, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { materia: '', cohorte: '', tipo: 'parcial', instancia: 1, fecha: '', titulo: '' },
  });

  useEffect(() => {
    if (evaluacion) {
      reset({
        materia: evaluacion.materia,
        cohorte: evaluacion.cohorte,
        tipo: evaluacion.tipo,
        instancia: evaluacion.instancia,
        fecha: evaluacion.fecha,
        titulo: evaluacion.titulo,
      });
    }
  }, [evaluacion, reset]);

  const selectedFecha = watch('fecha');

  const onSubmit = async (values: FormValues) => {
    const isPast = values.fecha && new Date(values.fecha) < new Date(new Date().toDateString());
    if (isPast && !pastDateWarning) {
      setPastDateWarning(true);
      return;
    }

    setMessage(null);
    try {
      if (isEdit && evaluacion) {
        await actualizarMutation.mutateAsync({ id: evaluacion.id, data: values });
        setMessage({ type: 'success', text: 'Evaluación actualizada correctamente' });
      } else {
        await crearMutation.mutateAsync(values);
        setMessage({ type: 'success', text: 'Evaluación creada correctamente' });
      }
      setPastDateWarning(false);
      onSuccess?.();
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 409) {
        setMessage({ type: 'error', text: 'Ya existe una evaluación con los mismos datos (materia × cohorte × tipo × instancia)' });
      } else {
        setMessage({ type: 'error', text: `Error al ${isEdit ? 'actualizar' : 'crear'} la evaluación` });
      }
    }
  };

  const isPending = crearMutation.isPending || actualizarMutation.isPending;

  const isPast = selectedFecha && new Date(selectedFecha) < new Date(new Date().toDateString());

  return (
    <Card>
      <CardHeader>
        <CardTitle>{isEdit ? 'Editar Evaluación' : 'Nueva Evaluación'}</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Materia"
            placeholder="Nombre de la materia"
            {...register('materia')}
            error={errors.materia?.message}
          />
          <Input
            label="Cohorte"
            placeholder="Nombre del cohorte"
            {...register('cohorte')}
            error={errors.cohorte?.message}
          />
          <div className="space-y-2">
            <label className="text-sm font-medium text-neutral-700">Tipo</label>
            <select
              {...register('tipo')}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              {TIPOS.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
            {errors.tipo && <p className="text-sm text-danger-600">{errors.tipo.message}</p>}
          </div>
          <Input
            label="Instancia"
            type="number"
            min={1}
            {...register('instancia')}
            error={errors.instancia?.message}
          />
          <Input
            label="Fecha"
            type="date"
            {...register('fecha')}
            error={errors.fecha?.message}
          />

          {isPast && pastDateWarning && (
            <div className="rounded-md bg-warning-50 p-3 text-sm text-warning-700">
              La fecha seleccionada está en el pasado. ¿Confirmar de todas formas?
              <div className="mt-2 flex gap-2">
                <button
                  type="button"
                  onClick={() => { setPastDateWarning(false); }}
                  className="text-sm font-medium text-primary-600 hover:underline"
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}

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
              : isEdit ? 'Actualizar evaluación' : 'Crear evaluación'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
