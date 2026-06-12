import { useState } from 'react';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { useAsignacionMasiva } from '../../hooks/useEquipos';

interface AsignacionMasivaFormProps {
  onSuccess?: () => void;
}

export function AsignacionMasivaForm({ onSuccess }: AsignacionMasivaFormProps) {
  const [docenteIds, setDocenteIds] = useState<string[]>([]);
  const [docenteSearch, setDocenteSearch] = useState('');
  const [materiaId, setMateriaId] = useState('');
  const [carreraId, setCarreraId] = useState('');
  const [cohorteId, setCohorteId] = useState('');
  const [rol, setRol] = useState('');
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string; errors?: unknown[] } | null>(null);

  const mutation = useAsignacionMasiva();

  const addDocente = (id: string) => {
    if (!docenteIds.includes(id)) {
      setDocenteIds((prev) => [...prev, id]);
    }
    setDocenteSearch('');
  };

  const removeDocente = (id: string) => {
    setDocenteIds((prev) => prev.filter((d) => d !== id));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (docenteIds.length === 0) return;
    setMessage(null);

    try {
      const result = await mutation.mutateAsync({
        docente_ids: docenteIds,
        materia_id: materiaId,
        carrera_id: carreraId,
        cohorte_id: cohorteId,
        rol,
        fecha_desde: fechaDesde,
        fecha_hasta: fechaHasta,
      });
      setMessage({
        type: 'success',
        text: `Se crearon ${result.count} asignaciones correctamente`,
        errors: result.errors,
      });
      onSuccess?.();
    } catch {
      setMessage({ type: 'error', text: 'Error de conexión. Los valores del formulario se conservan.' });
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Asignación Masiva</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-neutral-700">Docentes</label>
            <div className="mt-1 flex flex-wrap gap-2">
              {docenteIds.map((id) => (
                <span key={id} className="inline-flex items-center gap-1 rounded-full bg-primary-100 px-3 py-1 text-xs font-medium text-primary-700">
                  {id}
                  <button type="button" onClick={() => removeDocente(id)} className="ml-1 text-primary-500 hover:text-primary-700">×</button>
                </span>
              ))}
            </div>
            <div className="mt-2 flex gap-2">
              <Input
                value={docenteSearch}
                onChange={(e) => setDocenteSearch(e.target.value)}
                placeholder="Buscar docente..."
              />
              <Button
                type="button"
                variant="outline"
                onClick={() => docenteSearch && addDocente(docenteSearch)}
                disabled={!docenteSearch}
              >
                Agregar
              </Button>
            </div>
            {docenteIds.length === 0 && (
              <p className="mt-1 text-xs text-danger-600">Al menos 1 docente requerido</p>
            )}
          </div>

          <Input label="Materia ID" value={materiaId} onChange={(e) => setMateriaId(e.target.value)} />
          <Input label="Carrera ID" value={carreraId} onChange={(e) => setCarreraId(e.target.value)} />
          <Input label="Cohorte ID" value={cohorteId} onChange={(e) => setCohorteId(e.target.value)} />
          <Input label="Rol" value={rol} onChange={(e) => setRol(e.target.value)} placeholder="PROFESOR / TUTOR / NEXO / COORDINADOR" />
          <Input label="Fecha desde" type="date" value={fechaDesde} onChange={(e) => setFechaDesde(e.target.value)} />
          <Input label="Fecha hasta" type="date" value={fechaHasta} onChange={(e) => setFechaHasta(e.target.value)} />

          {message && (
            <div
              className={`rounded-md p-3 text-sm ${
                message.type === 'success' ? 'bg-success-50 text-success-600' : 'bg-danger-50 text-danger-600'
              }`}
            >
              <p>{message.text}</p>
              {message.errors && message.errors.length > 0 && (
                <details className="mt-2">
                  <summary className="cursor-pointer text-xs font-medium">
                    {message.errors.length} error(es)
                  </summary>
                  <ul className="mt-1 list-inside list-disc text-xs">
                    {message.errors.map((err, i) => (
                      <li key={i}>{JSON.stringify(err)}</li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          )}

          <Button type="submit" isLoading={mutation.isPending} disabled={docenteIds.length === 0 || mutation.isPending}>
            {mutation.isPending ? 'Asignando...' : `Asignar a ${docenteIds.length} docente(s)`}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
