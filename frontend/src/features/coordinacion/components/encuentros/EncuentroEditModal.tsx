import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { useEditarEncuentro } from '../../hooks/useEncuentros';
import type { Encuentro } from '../../types/encuentros.types';

const schema = z.object({
  estado: z.enum(['programado', 'realizado', 'cancelado']),
  enlace: z.string().url('URL inválida').optional().or(z.literal('')),
  grabacion: z.string().url('URL inválida').optional().or(z.literal('')),
  comentario_interno: z.string().optional(),
  aplicar_futuras: z.boolean().optional(),
});

type FormValues = z.infer<typeof schema>;

interface EncuentroEditModalProps {
  encuentro: Encuentro;
  esRecurrente?: boolean;
  onSuccess?: () => void;
  onClose?: () => void;
}

export function EncuentroEditModal({ encuentro, esRecurrente = false, onSuccess, onClose }: EncuentroEditModalProps) {
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);
  const mutation = useEditarEncuentro();

  const { register, watch, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      estado: encuentro.estado,
      enlace: encuentro.enlace ?? '',
      grabacion: encuentro.grabacion ?? '',
      comentario_interno: encuentro.comentario_interno ?? '',
      aplicar_futuras: false,
    },
  });

  useEffect(() => {
    reset({
      estado: encuentro.estado,
      enlace: encuentro.enlace ?? '',
      grabacion: encuentro.grabacion ?? '',
      comentario_interno: encuentro.comentario_interno ?? '',
      aplicar_futuras: false,
    });
  }, [encuentro, reset]);

  const watchEstado = watch('estado');

  const onSubmit = async (values: FormValues) => {
    if (values.estado === 'cancelado') {
      setShowCancelConfirm(true);
      return;
    }
    await doSubmit(values);
  };

  const doSubmit = async (values: FormValues) => {
    setMessage(null);
    try {
      const data: Partial<Encuentro> & { aplicar_futuras?: boolean } = {
        estado: values.estado,
        enlace: values.enlace || null,
        grabacion: values.grabacion || null,
        comentario_interno: values.comentario_interno || null,
      };
      if (esRecurrente && values.aplicar_futuras) {
        data.aplicar_futuras = true;
      }
      await mutation.mutateAsync({ id: encuentro.id, data });
      setMessage({ type: 'success', text: 'Encuentro actualizado correctamente' });
      onSuccess?.();
    } catch {
      setMessage({ type: 'error', text: 'Error al actualizar el encuentro' });
    }
  };

  return (
    <Card className="max-w-lg">
      <CardHeader>
        <CardTitle>Editar Encuentro</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {showCancelConfirm ? (
            <div className="rounded-md border border-amber-200 bg-amber-50 p-4">
              <p className="text-sm font-medium text-amber-800">¿Cancelar este encuentro?</p>
              <p className="mt-1 text-sm text-amber-600">Esta acción no se puede deshacer.</p>
              <div className="mt-3 flex gap-2">
                <Button type="button" variant="destructive" onClick={() => { setShowCancelConfirm(false); doSubmit(watch()); }}>
                  Sí, cancelar
                </Button>
                <Button type="button" variant="outline" onClick={() => setShowCancelConfirm(false)}>
                  No, mantener
                </Button>
              </div>
            </div>
          ) : (
            <>
              <div className="space-y-2">
                <label className="text-sm font-medium text-neutral-700">Estado</label>
                <div className="flex gap-2">
                  {(['programado', 'realizado', 'cancelado'] as const).map((est) => (
                    <label
                      key={est}
                      className={`flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2 text-sm transition-colors ${
                        watchEstado === est
                          ? 'border-primary-500 bg-primary-50 text-primary-700'
                          : 'border-neutral-300 bg-white text-neutral-700 hover:bg-neutral-50'
                      }`}
                    >
                      <input
                        type="radio"
                        value={est}
                        {...register('estado')}
                        className="sr-only"
                      />
                      {est === 'programado' ? 'Programado' : est === 'realizado' ? 'Realizado' : 'Cancelado'}
                    </label>
                  ))}
                </div>
              </div>

              <Input
                label="Enlace de videoconferencia"
                type="url"
                {...register('enlace')}
                error={errors.enlace?.message}
              />

              <Input
                label="Enlace de grabación"
                type="url"
                {...register('grabacion')}
                disabled={watchEstado !== 'realizado'}
                error={errors.grabacion?.message}
              />

              <div className="space-y-2">
                <label className="text-sm font-medium text-neutral-700">Comentario interno</label>
                <textarea
                  {...register('comentario_interno')}
                  className="flex min-h-[80px] w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm placeholder:text-neutral-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2"
                  placeholder="Notas internas..."
                />
              </div>

              {esRecurrente && (
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    {...register('aplicar_futuras')}
                    className="rounded border-neutral-300"
                  />
                  <span className="text-neutral-700">Aplicar cambios a todas las instancias futuras</span>
                </label>
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

              <div className="flex gap-2">
                <Button type="submit" isLoading={mutation.isPending} disabled={mutation.isPending}>
                  {mutation.isPending ? 'Guardando...' : 'Guardar cambios'}
                </Button>
                {onClose && (
                  <Button type="button" variant="outline" onClick={onClose}>
                    Cancelar
                  </Button>
                )}
              </div>
            </>
          )}
        </form>
      </CardContent>
    </Card>
  );
}
