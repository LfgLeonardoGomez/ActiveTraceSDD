import { useQuery, type UseQueryResult } from '@tanstack/react-query';
import api from '@/shared/services/api';
import { getAccessToken } from '@/shared/services/api';
import type { MeResponse } from '@/features/auth/types/auth.types';

export function useMeQuery(): UseQueryResult<MeResponse> {
  return useQuery<MeResponse>({
    queryKey: ['me'],
    queryFn: async () => {
      const { data } = await api.get<MeResponse>('/api/auth/me');
      return data;
    },
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    retry: 1,
    enabled: !!getAccessToken(),
  });
}
