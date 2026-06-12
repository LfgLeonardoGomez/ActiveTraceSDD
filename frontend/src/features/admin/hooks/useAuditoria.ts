import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getAccessToken } from '@/shared/services/api';
import * as api from '../services/auditoria.api';
import type {
  AccionPorDia,
  ComunicacionPorDocente,
  InteraccionPorDocenteMateria,
  UltimaAccion,
  AuditLogEntry,
  AuditLogFilters,
  CatalogoAccion,
} from '../types/auditoria.types';

const AUDITORIA_KEYS = {
  accionesPorDia: () => ['admin', 'auditoria', 'acciones-por-dia'] as const,
  comunicaciones: () => ['admin', 'auditoria', 'comunicaciones'] as const,
  interacciones: () => ['admin', 'auditoria', 'interacciones'] as const,
  ultimasAcciones: () => ['admin', 'auditoria', 'ultimas-acciones'] as const,
  log: (filters?: AuditLogFilters) => ['admin', 'auditoria', 'log', filters] as const,
  catalogo: () => ['admin', 'auditoria', 'catalogo'] as const,
};

export function useAccionesPorDia() {
  return useQuery<AccionPorDia[]>({
    queryKey: AUDITORIA_KEYS.accionesPorDia(),
    queryFn: api.getAccionesPorDia,
    staleTime: 5 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}

export function useComunicacionesPorDocente() {
  return useQuery<ComunicacionPorDocente[]>({
    queryKey: AUDITORIA_KEYS.comunicaciones(),
    queryFn: api.getComunicacionesPorDocente,
    staleTime: 5 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}

export function useInteraccionesPorDocenteMateria() {
  return useQuery<InteraccionPorDocenteMateria[]>({
    queryKey: AUDITORIA_KEYS.interacciones(),
    queryFn: api.getInteraccionesPorDocenteMateria,
    staleTime: 5 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}

export function useUltimasAcciones() {
  return useQuery<UltimaAccion[]>({
    queryKey: AUDITORIA_KEYS.ultimasAcciones(),
    queryFn: api.getUltimasAcciones,
    staleTime: 2 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}

export function useAuditLog(filters?: AuditLogFilters) {
  return useQuery<{ items: AuditLogEntry[]; total: number }>({
    queryKey: AUDITORIA_KEYS.log(filters),
    queryFn: () => api.getAuditLog(filters),
    staleTime: 2 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}

export function useCatalogoAcciones() {
  return useQuery<CatalogoAccion[]>({
    queryKey: AUDITORIA_KEYS.catalogo(),
    queryFn: api.getCatalogoAcciones,
    staleTime: 30 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}

export function useInvalidateAuditLog() {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ['admin', 'auditoria', 'log'] });
  };
}
