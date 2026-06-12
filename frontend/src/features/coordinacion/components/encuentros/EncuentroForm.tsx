import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { useCrearEncuentro } from '../../hooks/useEncuentros';

const schema = z.object({
  materia_id: z.string().min(1, 'Materia requerida'),
  fecha: z.string().min(1, 'Fecha requerida'),
  hora: z.string().min(1, 'Hora requerida'),
  titulo: z.string().min(1, 'Título requerido'),
  enlace: z.string().url('URL inválida').optional().or(z.literal('')),
});

type FormValues = z.infer<typeof schema>;

interface EncuentroFormProps {
  onSuccess?: () => void;
}

export function EncuentroForm({ onSuccess }: EncuentroFormProps) {
  const navigate = useNavigate();
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const mutation = useCrearEncuentro();
  const today = new Date().toISOString().split('T')[0];

  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (values: FormValues) => {
    setMessage(null);
    try {
      await mutation.mutateAsync(values);
      setMessage({ type: 'success', text: 'Encuentro creado correctamente' });
      onSuccess?.();
      navigate('/coordinacion/encuentros');
    } catch {
      setMessage({ type: 'error', text: 'Error al crear el encuentro' });
    }
  };

  const isPastDate = (date: string) => date < today;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Nuevo Encuentro</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Materia ID"
            {...register('materia_id')}
            error={errors.materia_id?.message}
          />
          <Input
            label="Fecha"
            type="date"
            min={today}
            {...register('fecha')}
            error={errors.fecha?.message}
            onChange={(e) => {
              if (isPastDate(e.target.value)) {
                setMessage({ type: 'error', text: 'La fecha es pasada — verificar' });
              }
              register('fecha').onChange(e);
            }}
          />
          {message?.type === 'error' && message.text.includes('pasada') && (
            <div className="rounded-md bg-amber-50 p-3 text-sm text-amber-700">
              {message.text}
            </div>
          )}
          <Input
            label="Hora"
            type="time"
            {...register('hora')}
            error={errors.hora?.message}
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

          {message && !message.text.includes('pasada') && (
            <div
              className={`rounded-md p-3 text-sm ${
                message.type === 'success' ? 'bg-success-50 text-success-600' : 'bg-danger-50 text-danger-600'
              }`}
            >
              {message.text}
            </div>
          )}

          <Button type="submit" isLoading={mutation.isPending} disabled={mutation.isPending}>
            {mutation.isPending ? 'Creando...' : 'Crear encuentro'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
