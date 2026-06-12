import { useOutletContext } from 'react-router-dom';
import { RankingTable } from './RankingTable';

export function RankingTab() {
  const { materiaId } = useOutletContext<{ materiaId: string }>();
  return <RankingTable materiaId={materiaId} />;
}
