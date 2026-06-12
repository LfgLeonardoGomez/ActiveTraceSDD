import { useMutation, useQueryClient } from '@tanstack/react-query';
import { importPreview, importConfirm, importFinalizacion } from '../services/comisiones.api';

export function useImportPreview() {
  return useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return importPreview(formData);
    },
  });
}

export function useImportConfirm(materiaId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (activities_selected: string[]) =>
      importConfirm({ materia_id: materiaId, activities_selected }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analisis', materiaId] });
    },
  });
}

export function useImportFinalizacion(materiaId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return importFinalizacion(formData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analisis', materiaId, 'tps-sin-corregir'] });
    },
  });
}
