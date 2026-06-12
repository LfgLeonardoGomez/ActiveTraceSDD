import { useQuery } from '@tanstack/react-query';
import { getTpsSinCorregir, getTpsSinCorregirExportUrl } from '../services/comisiones.api';
import type { TpsSinCorregirEntry } from '../types/comisiones.types';

export function useTpsSinCorregir(materiaId: string) {
  return useQuery<TpsSinCorregirEntry[]>({
    queryKey: ['analisis', materiaId, 'tps-sin-corregir'],
    queryFn: () => getTpsSinCorregir(materiaId),
    enabled: !!materiaId,
  });
}

export { getTpsSinCorregirExportUrl };
