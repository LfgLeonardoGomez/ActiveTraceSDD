import { useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { AvisoScopeSelector } from './AvisoScopeSelector';
import { useCrearAviso, useEditarAviso, useEliminarAviso } from '../../hooks/useAvisos';
import type { Aviso, AvisoFormData } from '../../types/avisos.types';

const schema = z.object({
  titulo: z.string().min(1, 'El título es requerido'),
  cuerpo: z.string().min(1, 'El cuerpo del aviso no puede estar vacío'),
  alcance: z.enum(['global', 'materia', 'cohorte']),
  materia_id: z.string().optional(),
  cohorte_id: z.string().optional(),
  roles_destinatarios: z.array(z.string()),
  severidad: z.enum(['informativo', 'advertencia', 'critico']),
  fecha_desde: z.string().optional(),
  fecha_hasta: z.string().optional(),
  requiere_ack: z.boolean(),
}).refine(
  (data) => {
    if (!data.fecha_desde || !data.fecha_hasta) return true;
    return data.fecha_hasta > data.fecha_desde;
  },
  { message: 'La fecha de fin debe ser posterior a la fecha de inicio', path: ['fecha_hasta'] },
);

type FormValues = z.infer<typeof schema>;

interface AvisoFormProps {
  aviso?: Aviso;
  onSuccess?: () => void;
}

const ALL_ROLES = ['TUTOR', 'PROFESOR', 'COORDINADOR', 'ADMIN', 'FINANZAS', 'NEXO'];

const MOCK_MATERIAS = [
  { id: 'mat-1', nombre: 'Matemática I' },
  { id: 'mat-2', nombre: 'Programación II' },
  { id: 'mat-3', nombre: 'Base de Datos' },
];

const MOCK_COHORTES = [
  { id: 'coh-1', nombre: 'MAR-2025' },
  { id: 'coh-2', nombre: 'AGO-2025' },
  { id: 'coh-3', nombre: 'MAR-2026' },
];

export function AvisoForm({ aviso, onSuccess }: AvisoFormProps) {
  const navigate = useNavigate();
  const crearAviso = useCrearAviso();
  const editarAviso = useEditarAviso();
  const eliminarAviso = useEliminarAviso();
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const isEdit = !!aviso;

  const defaultValues: FormValues = aviso
    ? {
        titulo: aviso.titulo,
        cuerpo: aviso.cuerpo,
        alcance: aviso.alcance,
        materia_id: aviso.materia_id ?? undefined,
        cohorte_id: aviso.cohorte_id ?? undefined,
        roles_destinatarios: aviso.roles_destinatarios,
        severidad: aviso.severidad,
        fecha_desde: aviso.fecha_desde ?? undefined,
        fecha_hasta: aviso.fecha_hasta ?? undefined,
        requiere_ack: aviso.requiere_ack,
      }
    : {
        titulo: '',
        cuerpo: '',
        alcance: 'global' as const,
        materia_id: undefined,
        cohorte_id: undefined,
        roles_destinatarios: [...ALL_ROLES],
        severidad: 'informativo' as const,
        fecha_desde: undefined,
        fecha_hasta: undefined,
        requiere_ack: false,
      };

  const { register, handleSubmit, control, watch, setValue, formState: { errors, isSubmitting } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues,
  });

  const alcance = watch('alcance');

  const submitForm = async (values: FormValues, estado: 'publicado' | 'borrador') => {
    setMessage(null);
    const payload: AvisoFormData = {
      ...values,
      estado,
      materia_id: values.alcance === 'materia' ? values.materia_id : undefined,
      cohorte_id: values.alcance === 'cohorte' ? values.cohorte_id : undefined,
    };

    if (payload.roles_destinatarios.length === 0) {
      payload.roles_destinatarios = [...ALL_ROLES];
    }

    try {
      if (isEdit && aviso) {
        await editarAviso.mutateAsync({ id: aviso.id, data: payload });
      } else {
        await crearAviso.mutateAsync(payload);
      }
      setMessage({ type: 'success', text: `Aviso ${estado === 'publicado' ? 'publicado' : 'guardado'} correctamente` });
      onSuccess?.();
      setTimeout(() => navigate('/coordinacion/avisos'), 1200);
    } catch {
      setMessage({ type: 'error', text: 'Error al guardar el aviso. Intentalo de nuevo.' });
    }
  };

  const handleDelete = async () => {
    if (!aviso) return;
    try {
      await eliminarAviso.mutateAsync(aviso.id);
      onSuccess?.();
      navigate('/coordinacion/avisos');
    } catch {
      setMessage({ type: 'error', text: 'Error al eliminar el aviso' });
    }
  };

  const isPending = crearAviso.isPending || editarAviso.isPending || eliminarAviso.isPending;

  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <CardTitle>{isEdit ? 'Editar aviso' : 'Nuevo aviso'}</CardTitle>
      </CardHeader>
      <CardContent>
        <form
          onSubmit={handleSubmit((values) => submitForm(values, 'publicado'))}
          className="space-y-6"
        >
          <Input
            label="Título"
            {...register('titulo')}
            error={errors.titulo?.message}
            placeholder="Título del aviso"
          />

          <div className="space-y-2">
            <label htmlFor="cuerpo" className="text-sm font-medium text-neutral-900">
              Cuerpo (markdown)
            </label>
            <textarea
              id="cuerpo"
              rows={6}
              className="flex w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm placeholder:text-neutral-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
              placeholder="Escribí el contenido del aviso. Soporta markdown."
              {...register('cuerpo')}
              aria-invalid={!!errors.cuerpo}
            />
            {errors.cuerpo && (
              <p className="text-sm text-danger-600">{errors.cuerpo.message}</p>
            )}
          </div>

          <Controller
            control={control}
            name="alcance"
            render={({ field }) => (
              <AvisoScopeSelector
                alcance={field.value}
                onAlcanceChange={field.onChange}
                materia_id={watch('materia_id') ?? ''}
                onMateriaChange={(val) => setValue('materia_id', val)}
                cohorte_id={watch('cohorte_id') ?? ''}
                onCohorteChange={(val) => setValue('cohorte_id', val)}
                roles={watch('roles_destinatarios')}
                onRolesChange={(roles) => setValue('roles_destinatarios', roles)}
                materias={MOCK_MATERIAS}
                cohortes={MOCK_COHORTES}
              />
            )}
          />

          <div className="space-y-2">
            <label htmlFor="severidad" className="text-sm font-medium text-neutral-900">
              Severidad
            </label>
            <select
              id="severidad"
              className="flex h-10 w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm"
              {...register('severidad')}
            >
              <option value="informativo">Informativo</option>
              <option value="advertencia">Advertencia</option>
              <option value="critico">Crítico</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
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
          </div>
          {errors.fecha_hasta && !errors.fecha_hasta.message?.includes('required') && (
            <p className="text-sm text-danger-600">{errors.fecha_hasta.message}</p>
          )}

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              className="text-primary-600 rounded"
              {...register('requiere_ack')}
            />
            <span className="text-sm font-medium text-neutral-900">
              Requiere confirmación de lectura (ack)
            </span>
          </label>

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

          <div className="flex flex-wrap gap-3">
            <Button
              type="submit"
              isLoading={isPending}
              disabled={isPending}
            >
              Publicar
            </Button>
            <Button
              type="button"
              variant="secondary"
              isLoading={isPending}
              disabled={isPending}
              onClick={handleSubmit((values) => submitForm(values, 'borrador'))}
            >
              Guardar borrador
            </Button>
            {isEdit && (
              <Button
                type="button"
                variant="destructive"
                disabled={isPending}
                onClick={() => setShowDeleteConfirm(true)}
              >
                Eliminar
              </Button>
            )}
            <Button
              type="button"
              variant="ghost"
              onClick={() => navigate('/coordinacion/avisos')}
            >
              Cancelar
            </Button>
          </div>
        </form>

        {showDeleteConfirm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="rounded-lg bg-white p-6 shadow-xl max-w-md w-full space-y-4">
              <p className="text-sm text-neutral-700">
                {aviso && `¿Eliminar el aviso "${aviso.titulo}"?`}
              </p>
              <div className="flex gap-3 justify-end">
                <Button variant="ghost" onClick={() => setShowDeleteConfirm(false)}>
                  Cancelar
                </Button>
                <Button
                  variant="destructive"
                  onClick={handleDelete}
                  isLoading={eliminarAviso.isPending}
                  disabled={eliminarAviso.isPending}
                >
                  Eliminar
                </Button>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
