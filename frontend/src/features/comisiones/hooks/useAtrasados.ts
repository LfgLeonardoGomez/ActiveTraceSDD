import { useQuery } from '@tanstack/react-query';
import { getAtrasados } from '../services/comisiones.api';
import type { Atrasado } from '../types/comisiones.types';

export function useAtrasados(materiaId: string) {
  return useQuery<Atrasado[]>({
    queryKey: ['analisis', materiaId, 'atrasados'],
    queryFn: () => getAtrasados(materiaId),
    enabled: !!materiaId,
  });
}
