import { useState } from 'react';
import { Spinner } from '@/shared/components/ui/Spinner';
import { cn } from '@/lib/utils';
import { useImportPreview } from '../hooks/useCalificaciones';
import type { ImportPreviewResponse, ImportError } from '../types/comisiones.types';
import axios from 'axios';
import { AlertCircle } from 'lucide-react';

interface GradeUploaderProps {
  onPreview: (response: ImportPreviewResponse) => void;
}

export function GradeUploader({ onPreview }: GradeUploaderProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const previewMutation = useImportPreview();

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext !== 'csv' && ext !== 'xlsx') {
      setError('Formato de archivo no soportado. Usá .csv o .xlsx');
      e.target.value = '';
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const response = await previewMutation.mutateAsync(file);
      onPreview(response);
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        if (detail) {
          setError(detail);
        } else if (err.response?.data?.errors) {
          setError(
            (err.response.data.errors as ImportError[])
              .map((er) => `Fila ${er.row}: ${er.mensaje}`)
              .join('\n'),
          );
        } else if (!err.response) {
          setError('Error de conexión. Verificá tu conexión e intentá de nuevo.');
        } else {
          setError('Error al procesar el archivo. Verificá el formato.');
        }
      } else {
        setError('Error al procesar el archivo. Verificá el formato.');
      }
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-neutral-700">
        Subir archivo de calificaciones
      </label>

      <input
        type="file"
        accept=".csv,.xlsx"
        onChange={handleFile}
        disabled={isUploading}
        className={cn(
          'block w-full text-sm file:mr-4 file:rounded-md file:border-0 file:px-4 file:py-2 file:text-sm',
          'file:bg-primary-50 file:text-primary-700 file:cursor-pointer hover:file:bg-primary-100',
          isUploading && 'cursor-not-allowed opacity-50',
        )}
      />

      {isUploading && (
        <div className="flex items-center gap-2 text-sm text-neutral-600">
          <Spinner size="sm" />
          <span>Procesando archivo...</span>
        </div>
      )}

      {error && (
        <div className="flex items-start gap-2 rounded-md bg-danger-50 p-3 text-sm text-danger-600">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span className="whitespace-pre-line">{error}</span>
        </div>
      )}
    </div>
  );
}
