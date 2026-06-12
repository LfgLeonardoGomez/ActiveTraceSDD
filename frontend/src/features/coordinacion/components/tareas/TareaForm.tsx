import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { useAsignarTarea } from '../../hooks/useTareas';

const schema = z.object({
  asignado_id: z.string().min(1, 'Docente requerido'),
  titulo: z.string().min(1, 'Título requerido'),
  materia: z.string().optional(),
  descripcion: z.string().optional(),
  fecha_limite: z.string().refine(
    (val) => !val || new Date(val) > new Date(),
    { message: 'La fecha límite debe ser futura' },
  ),
  prioridad: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

export function TareaForm() {
  const navigate = useNavigate();
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [docenteSearch, setDocenteSearch] = useState('');
  const [showDocenteDropdown, setShowDocenteDropdown] = useState(false);
  const mutation = useAsignarTarea();

  const { register, handleSubmit, setValue, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (values: FormValues) => {
    setMessage(null);
    try {
      await mutation.mutateAsync(values);
      setMessage({ type: 'success', text: 'Tarea asignada correctamente' });
      setTimeout(() => { navigate('/coordinacion/tareas'); }, 1500);
    } catch {
      setMessage({ type: 'error', text: 'Error al asignar la tarea' });
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Asignar tarea</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium leading-none">Docente</label>
            <div className="relative">
              <input
                value={docenteSearch}
                onChange={(e) => {
                  setDocenteSearch(e.target.value);
                  setShowDocenteDropdown(e.target.value.length >= 3);
                }}
                placeholder="Buscar docente (mín. 3 caracteres)"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              />
              {showDocenteDropdown && (
                <div className="absolute left-0 top-full z-10 mt-1 w-full rounded-md border border-neutral-200 bg-white shadow-lg">
                  <div className="px-3 py-2 text-xs text-neutral-400">
                    Escribí al menos 3 caracteres para buscar...
                  </div>
                </div>
              )}
            </div>
            {errors.asignado_id && (
              <p className="text-sm text-danger-600" role="alert">{errors.asignado_id.message}</p>
            )}
          </div>

          <Input
            label="Título"
            {...register('titulo')}
            error={errors.titulo?.message}
            placeholder="Ej: Corregir TP2"
          />

          <Input
            label="Materia (opcional)"
            {...register('materia')}
            error={errors.materia?.message}
            placeholder="Ej: Matemática I"
          />

          <div className="space-y-2">
            <label className="text-sm font-medium leading-none">Descripción (opcional)</label>
            <textarea
              {...register('descripcion')}
              rows={3}
              placeholder="Detalles de la tarea..."
              className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            />
          </div>

          <Input
            label="Fecha límite"
            type="date"
            {...register('fecha_limite')}
            error={errors.fecha_limite?.message}
          />

          <div className="space-y-2">
            <label className="text-sm font-medium leading-none">Prioridad</label>
            <select
              {...register('prioridad')}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              <option value="">Normal</option>
              <option value="baja">Baja</option>
              <option value="normal">Normal</option>
              <option value="alta">Alta</option>
              <option value="urgente">Urgente</option>
            </select>
          </div>

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
            {mutation.isPending ? 'Asignando tarea...' : 'Asignar tarea'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
