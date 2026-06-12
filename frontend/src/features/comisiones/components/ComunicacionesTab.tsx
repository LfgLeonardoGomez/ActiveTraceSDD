import { useLocation, useNavigate, useOutletContext } from 'react-router-dom';
import { ComunicacionTracking } from './ComunicacionTracking';
import { LoteActions } from './LoteActions';
import { useComunicacionEstado } from '../hooks/useComunicaciones';
import { MailQuestion } from 'lucide-react';

export function ComunicacionesTab() {
  const { materiaId } = useOutletContext<{ materiaId: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const loteId = (location.state as { loteId?: string })?.loteId;

  const { data: lote } = useComunicacionEstado(loteId ?? null);

  if (!loteId) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <MailQuestion className="h-12 w-12 text-neutral-300" />
        <p className="mt-4 text-sm font-medium text-neutral-600">No hay comunicaciones activas</p>
        <p className="mt-1 text-xs text-neutral-500">
          Seleccioná alumnos atrasados y enviá una comunicación desde la pestaña Atrasados.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <LoteActions
        loteId={loteId}
        loteEstado={lote?.estado ?? 'pendiente'}
        itemCount={lote?.items.length ?? 0}
      />
      <ComunicacionTracking
        loteId={loteId}
        onBack={() => navigate(`/comisiones/${materiaId}/atrasados`)}
      />
    </div>
  );
}
