import { useOutletContext } from 'react-router-dom';
import { TpsSinCorregirTable } from './TpsSinCorregirTable';

export function TpsSinCorregirTab() {
  const { materiaId } = useOutletContext<{ materiaId: string }>();
  return <TpsSinCorregirTable materiaId={materiaId} />;
}
