import { useMutation, useQueryClient } from '@tanstack/react-query';
import { clearData } from '../services/comisiones.api';

export function useClearData(materiaId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => clearData(materiaId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analisis', materiaId] });
      queryClient.invalidateQueries({ queryKey: ['umbral', materiaId] });
    },
  });
}
