import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Spinner } from '@/shared/components/ui/Spinner';
import { useGuardias, useRegistrarGuardia } from '../../hooks/useEncuentros';
import type { GuardiaFilters } from '../../types/encuentros.types';

const guardiaSchema = z.object({
  tutor_id: z.string().min(1, 'Tutor requerido'),
  materia_id: z.string().min(1, 'Materia requerida'),
  dia: z.string().min(1, 'Día requerido'),
  horario_desde: z.string().min(1, 'Horario desde requerido'),
  horario_hasta: z.string().min(1, 'Horario hasta requerido'),
  estado: z.string().default('activa'),
  comentarios: z.string().optional(),
}).refine(
  (data) => !data.horario_desde || !data.horario_hasta || data.horario_hasta > data.horario_desde,
  { message: 'Horario hasta debe ser posterior a horario desde', path: ['horario_hasta'] },
);

type GuardiaFormValues = z.infer<typeof guardiaSchema>;

export function GuardiaTable() {
  const [filters, setFilters] = useState<GuardiaFilters>({});
  const [showForm, setShowForm] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const { data: guardias, isLoading, isError, refetch } = useGuardias(filters);
  const mutation = useRegistrarGuardia();

  const { register, handleSubmit, reset, formState: { errors } } = useForm<GuardiaFormValues>({
    resolver: zodResolver(guardiaSchema),
    defaultValues: { estado: 'activa' },
  });

  const onSubmitGuardia = async (values: GuardiaFormValues) => {
    setMessage(null);
    try {
      await mutation.mutateAsync(values);
      setMessage({ type: 'success', text: 'Guardia registrada correctamente' });
      reset();
      setShowForm(false);
    } catch {
      setMessage({ type: 'error', text: 'Error al registrar la guardia' });
    }
  };

  const handleExportCsv = () => {
    if (!guardias || guardias.length === 0) return;
    const headers = ['Tutor', 'Materia', 'Día', 'Horario Desde', 'Horario Hasta', 'Estado', 'Comentarios'];
    const rows = guardias.map((g) => [
      g.tutor, g.materia, g.dia, g.horario_desde, g.horario_hasta, g.estado, g.comentarios ?? '',
    ]);
    const csv = [headers.join(','), ...rows.map((r) => r.map((c) => `"${c}"`).join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'guardias.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-neutral-900">Guardias</h2>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowForm(true)}>
            + Registrar guardia
          </Button>
          <Button variant="outline" onClick={handleExportCsv} disabled={!guardias || guardias.length === 0}>
            Exportar CSV
          </Button>
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <Input
          placeholder="Tutor..."
          className="w-48"
          value={filters.tutor_id ?? ''}
          onChange={(e) => { setFilters((f) => ({ ...f, tutor_id: e.target.value || undefined })); }}
        />
        <Input
          placeholder="Materia..."
          className="w-48"
          value={filters.materia_id ?? ''}
          onChange={(e) => { setFilters((f) => ({ ...f, materia_id: e.target.value || undefined })); }}
        />
        <Input
          type="date"
          className="w-44"
          value={filters.fecha_desde ?? ''}
          onChange={(e) => { setFilters((f) => ({ ...f, fecha_desde: e.target.value || undefined })); }}
        />
        <Input
          type="date"
          className="w-44"
          value={filters.fecha_hasta ?? ''}
          onChange={(e) => { setFilters((f) => ({ ...f, fecha_hasta: e.target.value || undefined })); }}
        />
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Registrar Guardia</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmitGuardia)} className="space-y-4">
              <Input
                label="Tutor ID"
                {...register('tutor_id')}
                error={errors.tutor_id?.message}
              />
              <Input
                label="Materia ID"
                {...register('materia_id')}
                error={errors.materia_id?.message}
              />
              <Input
                label="Día"
                type="date"
                {...register('dia')}
                error={errors.dia?.message}
              />
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Horario desde"
                  type="time"
                  {...register('horario_desde')}
                  error={errors.horario_desde?.message}
                />
                <Input
                  label="Horario hasta"
                  type="time"
                  {...register('horario_hasta')}
                  error={errors.horario_hasta?.message}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-neutral-700">Comentarios</label>
                <textarea
                  {...register('comentarios')}
                  className="flex min-h-[60px] w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm placeholder:text-neutral-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2"
                />
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

              <div className="flex gap-2">
                <Button type="submit" isLoading={mutation.isPending} disabled={mutation.isPending}>
                  {mutation.isPending ? 'Registrando...' : 'Registrar guardia'}
                </Button>
                <Button type="button" variant="outline" onClick={() => { setShowForm(false); reset(); }}>
                  Cancelar
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-12 animate-pulse rounded-md bg-neutral-100" />
          ))}
        </div>
      ) : isError ? (
        <div className="rounded-lg border border-danger-200 bg-danger-50 p-6 text-center">
          <p className="text-danger-600">Error al cargar guardias</p>
          <button onClick={() => refetch()} className="mt-2 text-sm font-medium text-primary-600 hover:underline">
            Reintentar
          </button>
        </div>
      ) : !guardias || guardias.length === 0 ? (
        <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-6 text-center">
          <p className="text-neutral-600">No hay guardias registradas</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-200 text-left">
                <th className="pb-3 pr-4 font-medium text-neutral-600">Tutor</th>
                <th className="pb-3 pr-4 font-medium text-neutral-600">Materia</th>
                <th className="pb-3 pr-4 font-medium text-neutral-600">Carrera/Cohorte</th>
                <th className="pb-3 pr-4 font-medium text-neutral-600">Día</th>
                <th className="pb-3 pr-4 font-medium text-neutral-600">Horario</th>
                <th className="pb-3 pr-4 font-medium text-neutral-600">Estado</th>
                <th className="pb-3 font-medium text-neutral-600">Comentarios</th>
              </tr>
            </thead>
            <tbody>
              {guardias.map((g) => (
                <tr key={g.id} className="border-b border-neutral-100 hover:bg-neutral-50">
                  <td className="py-3 pr-4 text-neutral-900">{g.tutor}</td>
                  <td className="py-3 pr-4 text-neutral-900">{g.materia}</td>
                  <td className="py-3 pr-4 text-neutral-600">{g.carrera}/{g.cohorte}</td>
                  <td className="py-3 pr-4 text-neutral-600">{new Date(g.dia).toLocaleDateString()}</td>
                  <td className="py-3 pr-4 text-neutral-600">{g.horario_desde} - {g.horario_hasta}</td>
                  <td className="py-3 pr-4">
                    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                      g.estado === 'activa' ? 'bg-green-100 text-green-700' : 'bg-neutral-100 text-neutral-600'
                    }`}>
                      {g.estado}
                    </span>
                  </td>
                  <td className="py-3 text-neutral-600">{g.comentarios ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
