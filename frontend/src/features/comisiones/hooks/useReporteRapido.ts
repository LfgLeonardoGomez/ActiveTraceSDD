import { useQuery } from '@tanstack/react-query';
import { getReporteRapido } from '../services/comisiones.api';
import type { ReporteRapido } from '../types/comisiones.types';

export function useReporteRapido(materiaId: string) {
  return useQuery<ReporteRapido>({
    queryKey: ['analisis', materiaId, 'reporte-rapido'],
    queryFn: () => getReporteRapido(materiaId),
    enabled: !!materiaId,
  });
}
