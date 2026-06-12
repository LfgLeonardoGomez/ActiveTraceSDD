import { useQuery } from '@tanstack/react-query';
import { getNotasFinales, getNotasFinalesExportUrl } from '../services/comisiones.api';
import type { NotaFinal } from '../types/comisiones.types';

export function useNotasFinales(materiaId: string) {
  return useQuery<NotaFinal[]>({
    queryKey: ['analisis', materiaId, 'notas-finales'],
    queryFn: () => getNotasFinales(materiaId),
    enabled: !!materiaId,
  });
}

export { getNotasFinalesExportUrl };
