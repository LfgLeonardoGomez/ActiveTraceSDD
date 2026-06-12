import { useQuery } from '@tanstack/react-query';
import { getMisComisiones } from '../services/comisiones.api';
import { getAccessToken } from '@/shared/services/api';
import type { MateriaCohorte } from '../types/comisiones.types';

export function useComisiones() {
  return useQuery<MateriaCohorte[]>({
    queryKey: ['comisiones', 'materias'],
    queryFn: getMisComisiones,
    staleTime: 5 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}
