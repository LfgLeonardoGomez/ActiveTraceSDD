import { useQuery } from '@tanstack/react-query';
import { getRanking } from '../services/comisiones.api';
import type { RankingEntry } from '../types/comisiones.types';

export function useRanking(materiaId: string) {
  return useQuery<RankingEntry[]>({
    queryKey: ['analisis', materiaId, 'ranking'],
    queryFn: () => getRanking(materiaId),
    enabled: !!materiaId,
  });
}
