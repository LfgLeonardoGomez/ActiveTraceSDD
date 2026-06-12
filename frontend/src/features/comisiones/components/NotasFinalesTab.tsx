import { useOutletContext } from 'react-router-dom';
import { NotasFinalesTable } from './NotasFinalesTable';

export function NotasFinalesTab() {
  const { materiaId } = useOutletContext<{ materiaId: string }>();
  return <NotasFinalesTable materiaId={materiaId} />;
}
