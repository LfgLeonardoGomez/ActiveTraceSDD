import { useState } from 'react';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { useActualizarVigencia } from '../../hooks/useEquipos';

export function VigenciaEditor() {
  const [equipoId, setEquipoId] = useState('');
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);

  const mutation = useActualizarVigencia();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (fechaHasta <= fechaDesde) {
      setMessage({ type: 'error', text: 'La fecha hasta debe ser posterior a la fecha desde' });
      return;
    }

    if (!showConfirm) {
      setShowConfirm(true);
      return;
    }

    setMessage(null);
    mutation.mutateAsync({ equipo_id: equipoId, fecha_desde: fechaDesde, fecha_hasta: fechaHasta })
      .then((result) => {
        setMessage({ type: 'success', text: `Vigencia actualizada para ${result.updated_count} asignaciones` });
        setShowConfirm(false);
      })
      .catch(() => {
        setMessage({ type: 'error', text: 'Error al actualizar la vigencia' });
      });
  };

  const hasSelection = !!equipoId && !!fechaDesde && !!fechaHasta;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Editor de Vigencia</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Equipo ID"
            value={equipoId}
            onChange={(e) => setEquipoId(e.target.value)}
            placeholder="Seleccioná un equipo (materia×cohorte)"
          />
          <Input
            label="Fecha desde"
            type="date"
            value={fechaDesde}
            onChange={(e) => setFechaDesde(e.target.value)}
          />
          <Input
            label="Fecha hasta"
            type="date"
            value={fechaHasta}
            onChange={(e) => setFechaHasta(e.target.value)}
          />

          {message && (
            <div
              className={`rounded-md p-3 text-sm ${
                message.type === 'success' ? 'bg-success-50 text-success-600' : 'bg-danger-50 text-danger-600'
              }`}
            >
              {message.text}
              {message.type === 'error' && (
                <button
                  onClick={() => mutation.mutateAsync({ equipo_id: equipoId, fecha_desde: fechaDesde, fecha_hasta: fechaHasta })}
                  className="ml-2 underline"
                >
                  Reintentar
                </button>
              )}
            </div>
          )}

          {showConfirm && (
            <div className="rounded-md bg-warning-50 p-3 text-sm text-warning-700">
              ¿Confirmás la actualización de vigencia para {equipoId}?
              <div className="mt-2 flex gap-2">
                <Button type="submit">Confirmar</Button>
                <Button type="button" variant="outline" onClick={() => setShowConfirm(false)}>
                  Cancelar
                </Button>
              </div>
            </div>
          )}

          <Button type="submit" isLoading={mutation.isPending} disabled={!hasSelection || mutation.isPending}>
            {mutation.isPending ? 'Actualizando...' : 'Actualizar vigencia'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
