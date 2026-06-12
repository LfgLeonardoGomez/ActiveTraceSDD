import { useQuery } from '@tanstack/react-query';
import { getMonitor } from '../services/comisiones.api';
import type { MonitorFilters, MonitorPaginatedResponse } from '../types/comisiones.types';

export function useMonitor(materiaId: string, filters: MonitorFilters, page: number, esCoordinador = false) {
  return useQuery<MonitorPaginatedResponse>({
    queryKey: ['analisis', materiaId, 'monitor', filters, page, esCoordinador],
    queryFn: () => getMonitor(materiaId, filters, page, esCoordinador),
    enabled: !!materiaId,
    placeholderData: (prev) => prev,
  });
}
