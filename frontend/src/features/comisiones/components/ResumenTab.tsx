import { useOutletContext } from 'react-router-dom';
import { ReportesSummary } from './ReportesSummary';

export function ResumenTab() {
  const { materiaId } = useOutletContext<{ materiaId: string }>();
  return <ReportesSummary materiaId={materiaId} />;
}
