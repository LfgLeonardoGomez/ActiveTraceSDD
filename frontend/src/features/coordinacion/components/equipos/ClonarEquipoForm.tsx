import { useState } from 'react';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { useClonarEquipo, useAsignaciones } from '../../hooks/useEquipos';

interface ClonarEquipoFormProps {
  onSuccess?: () => void;
}

export function ClonarEquipoForm({ onSuccess }: ClonarEquipoFormProps) {
  const [origenMateriaId, setOrigenMateriaId] = useState('');
  const [origenCohorteId, setOrigenCohorteId] = useState('');
  const [destinoMateriaId, setDestinoMateriaId] = useState('');
  const [destinoCohorteId, setDestinoCohorteId] = useState('');
  const [showDestinoWarning, setShowDestinoWarning] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const mutation = useClonarEquipo();
  const { data: destinoAsignaciones } = useAsignaciones(
    destinoMateriaId && destinoCohorteId ? { materia_id: destinoMateriaId, cohorte_id: destinoCohorteId } : undefined,
  );

  const origenEmpty = origenMateriaId && origenCohorteId;
  const destinoHasAsignaciones = destinoAsignaciones && destinoAsignaciones.length > 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (origenMateriaId === destinoMateriaId && origenCohorteId === destinoCohorteId) {
      setMessage({ type: 'error', text: 'El equipo origen y destino no pueden ser el mismo' });
      return;
    }

    if (destinoHasAsignaciones && !confirmed) {
      setShowDestinoWarning(true);
      return;
    }

    setMessage(null);
    try {
      const result = await mutation.mutateAsync({
        origen: { materia_id: origenMateriaId, cohorte_id: origenCohorteId },
        destino: { materia_id: destinoMateriaId, cohorte_id: destinoCohorteId },
      });
      setMessage({ type: 'success', text: `Equipo clonado correctamente — ${result.asignaciones_creadas} asignaciones creadas` });
      onSuccess?.();
    } catch {
      setMessage({ type: 'error', text: 'Error al clonar el equipo' });
    }
  };

  const canClone = origenMateriaId && origenCohorteId && destinoMateriaId && destinoCohorteId;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Clonar Equipo</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="rounded-md border border-neutral-200 p-4">
            <h4 className="mb-3 text-sm font-medium text-neutral-700">Equipo origen</h4>
            <Input label="Materia ID" value={origenMateriaId} onChange={(e) => setOrigenMateriaId(e.target.value)} />
            <Input label="Cohorte ID" value={origenCohorteId} onChange={(e) => setOrigenCohorteId(e.target.value)} />
            {origenEmpty && (
              <p className="mt-1 text-xs text-neutral-500">Seleccioná un equipo para clonar</p>
            )}
          </div>

          <div className="rounded-md border border-neutral-200 p-4">
            <h4 className="mb-3 text-sm font-medium text-neutral-700">Equipo destino</h4>
            <Input label="Materia ID" value={destinoMateriaId} onChange={(e) => setDestinoMateriaId(e.target.value)} />
            <Input label="Cohorte ID" value={destinoCohorteId} onChange={(e) => setDestinoCohorteId(e.target.value)} />
            {showDestinoWarning && destinoHasAsignaciones && (
              <div className="mt-2 rounded-md bg-warning-50 p-3 text-sm text-warning-700">
                El equipo destino ya tiene {destinoAsignaciones.length} asignaciones. ¿Clonar de todas formas?
                <div className="mt-2 flex gap-2">
                  <Button type="submit" variant="outline" onClick={() => { setConfirmed(true); }}>
                    Clonar de todas formas
                  </Button>
                  <Button type="button" variant="outline" onClick={() => setShowDestinoWarning(false)}>
                    Cancelar
                  </Button>
                </div>
              </div>
            )}
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

          <Button type="submit" isLoading={mutation.isPending} disabled={!canClone || mutation.isPending}>
            {mutation.isPending ? 'Clonando equipo...' : 'Clonar equipo'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
