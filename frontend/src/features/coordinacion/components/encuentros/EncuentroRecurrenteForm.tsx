import { useState, useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Spinner } from '@/shared/components/ui/Spinner';
import { useCrearRecurrente } from '../../hooks/useEncuentros';
import type { SerieRecurrenteRequest } from '../../types/encuentros.types';

const DIAS = [
  { value: 1, label: 'Lunes' },
  { value: 2, label: 'Martes' },
  { value: 3, label: 'Miércoles' },
  { value: 4, label: 'Jueves' },
  { value: 5, label: 'Viernes' },
] as const;

const schema = z.object({
  materia_id: z.string().min(1, 'Materia requerida'),
  dia_semana: z.coerce.number().int().min(1).max(5),
  horario: z.string().min(1, 'Horario requerido'),
  fecha_inicio: z.string().min(1, 'Fecha de inicio requerida'),
  semanas: z.coerce.number().int().min(1, 'Mínimo 1 semana').max(16, 'Máximo 16 semanas'),
  titulo: z.string().min(1, 'Título requerido'),
  enlace: z.string().url('URL inválida').optional().or(z.literal('')),
});

type FormValues = z.infer<typeof schema>;

interface EncuentroRecurrenteFormProps {
  onSuccess?: () => void;
}

export function EncuentroRecurrenteForm({ onSuccess }: EncuentroRecurrenteFormProps) {
  const navigate = useNavigate();
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const mutation = useCrearRecurrente();
  const today = new Date().toISOString().split('T')[0];

  const { register, watch, handleSubmit, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { semanas: 1, dia_semana: 1 },
  });

  const watchedFechaInicio = watch('fecha_inicio');
  const watchedSemanas = watch('semanas');
  const watchedDia = watch('dia_semana');

  const previewDates = useMemo(() => {
    if (!watchedFechaInicio || !watchedSemanas || !watchedDia) return [];
    const dates: string[] = [];
    const start = new Date(watchedFechaInicio);
    for (let i = 0; i < watchedSemanas; i++) {
      const d = new Date(start);
      d.setDate(d.getDate() + i * 7);
      dates.push(d.toLocaleDateString('es-AR', { weekday: 'long', day: 'numeric', month: 'long' }));
    }
    return dates;
  }, [watchedFechaInicio, watchedSemanas, watchedDia]);

  const onSubmit = async (values: FormValues) => {
    setMessage(null);
    try {
      const payload: SerieRecurrenteRequest & { enlace?: string } = {
        materia_id: values.materia_id,
        dia_semana: values.dia_semana as 1 | 2 | 3 | 4 | 5,
        horario: values.horario,
        fecha_inicio: values.fecha_inicio,
        semanas: values.semanas,
        titulo: values.titulo,
      };
      if (values.enlace) payload.enlace = values.enlace;
      const result = await mutation.mutateAsync(payload);
      setMessage({ type: 'success', text: `Serie creada correctamente — ${result.count} instancias generadas` });
      onSuccess?.();
      navigate('/coordinacion/encuentros');
    } catch {
      setMessage({ type: 'error', text: 'Error al crear la serie recurrente' });
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Crear Serie Recurrente</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Materia ID"
            {...register('materia_id')}
            error={errors.materia_id?.message}
          />

          <div className="space-y-2">
            <label className="text-sm font-medium text-neutral-700">Día de la semana</label>
            <div className="flex flex-wrap gap-2">
              {DIAS.map((d) => (
                <label
                  key={d.value}
                  className={`flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2 text-sm transition-colors ${
                    watchedDia === d.value
                      ? 'border-primary-500 bg-primary-50 text-primary-700'
                      : 'border-neutral-300 bg-white text-neutral-700 hover:bg-neutral-50'
                  }`}
                >
                  <input
                    type="radio"
                    value={d.value}
                    {...register('dia_semana')}
                    className="sr-only"
                  />
                  {d.label}
                </label>
              ))}
            </div>
          </div>

          <Input
            label="Horario"
            type="time"
            {...register('horario')}
            error={errors.horario?.message}
          />

          <Input
            label="Fecha de inicio"
            type="date"
            {...register('fecha_inicio')}
            error={errors.fecha_inicio?.message}
          />

          {watchedFechaInicio && watchedFechaInicio < today && (
            <div className="rounded-md bg-amber-50 p-3 text-sm text-amber-700">
              La fecha de inicio es pasada. Verificar que sea correcta.
            </div>
          )}

          <Input
            label="Semanas (1-16)"
            type="number"
            min={1}
            max={16}
            {...register('semanas')}
            error={errors.semanas?.message}
          />

          <Input
            label="Título"
            {...register('titulo')}
            error={errors.titulo?.message}
          />

          <Input
            label="Enlace de videoconferencia"
            type="url"
            placeholder="https://meet.google.com/..."
            {...register('enlace')}
            error={errors.enlace?.message}
          />

          {previewDates.length > 0 && (
            <div className="rounded-md border border-neutral-200 bg-neutral-50 p-4">
              <p className="mb-2 text-sm font-medium text-neutral-700">Vista previa — {previewDates.length} instancias</p>
              <ul className="max-h-32 space-y-1 overflow-y-auto text-sm text-neutral-600">
                {previewDates.map((d, i) => (
                  <li key={i} className="flex items-center gap-2">
                    <span className="size-1.5 rounded-full bg-primary-400" />
                    {d}
                  </li>
                ))}
              </ul>
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

          {mutation.isPending && (
            <div className="flex items-center gap-2 rounded-md bg-primary-50 p-3 text-sm text-primary-700">
              <Spinner size="sm" />
              Generando instancias...
            </div>
          )}

          <Button type="submit" isLoading={mutation.isPending} disabled={mutation.isPending}>
            {mutation.isPending
              ? 'Generando...'
              : `Crear serie${previewDates.length > 0 ? ` (${previewDates.length} instancias)` : ''}`}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
