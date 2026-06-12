import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getUmbral, updateUmbral } from '../services/comisiones.api';
import type { Umbral } from '../types/comisiones.types';

export function useUmbral(materiaId: string) {
  return useQuery<Umbral>({
    queryKey: ['umbral', materiaId],
    queryFn: () => getUmbral(materiaId),
    enabled: !!materiaId,
  });
}

export function useUmbralMutation(materiaId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (umbral_pct: number) => updateUmbral(materiaId, { umbral_pct }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['umbral', materiaId] });
    },
  });
}
