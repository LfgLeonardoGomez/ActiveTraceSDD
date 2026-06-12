import { useQuery } from '@tanstack/react-query';
import { useDebounce } from '@/shared/hooks/useDebounce';
import { getAccessToken } from '@/shared/services/api';
import * as api from '../services/monitor.api';
import type {
  MonitorFilters,
  MonitorEntry,
  AuditoriaEntry,
  PaginatedResponse,
} from '../types/monitor.types';

const MONITOR_KEYS = {
  general: (filters?: MonitorFilters, page?: number) =>
    ['coordinacion', 'monitor', 'general', filters, page] as const,
  auditoria: (filters?: MonitorFilters, page?: number) =>
    ['coordinacion', 'monitor', 'auditoria', filters, page] as const,
};

export function useMonitorGeneral(filters: MonitorFilters = {}, page = 1) {
  const debouncedFilters = useDebounce(filters, 300);

  return useQuery<PaginatedResponse<MonitorEntry>>({
    queryKey: MONITOR_KEYS.general(debouncedFilters, page),
    queryFn: () => api.getMonitorGeneral(debouncedFilters, page),
    enabled: !!getAccessToken(),
    staleTime: 5 * 60 * 1000,
    placeholderData: (prev) => prev,
  });
}

export function useAuditoria(filters: MonitorFilters = {}, page = 1) {
  const debouncedFilters = useDebounce(filters, 300);

  return useQuery<PaginatedResponse<AuditoriaEntry>>({
    queryKey: MONITOR_KEYS.auditoria(debouncedFilters, page),
    queryFn: () => api.getAuditoria(debouncedFilters, page),
    enabled: !!getAccessToken(),
    staleTime: 5 * 60 * 1000,
    placeholderData: (prev) => prev,
  });
}
