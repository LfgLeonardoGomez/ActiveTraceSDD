import { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { GradeUploader } from './GradeUploader';
import { ActivitySelector } from './ActivitySelector';
import { Button } from '@/shared/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Spinner } from '@/shared/components/ui/Spinner';
import { useImportFinalizacion } from '../hooks/useCalificaciones';
import type { ImportPreviewResponse, TpsSinCorregirEntry } from '../types/comisiones.types';
import { Download } from 'lucide-react';
import { getTpsSinCorregirExportUrl } from '../services/comisiones.api';
import axios from 'axios';

type ImportState = 'idle' | 'previewing' | 'importing' | 'success' | 'error';

export function ImportarTab() {
  const { materiaId } = useOutletContext<{ materiaId: string }>();
  const [state, setState] = useState<ImportState>('idle');
  const [preview, setPreview] = useState<ImportPreviewResponse | null>(null);
  const finalizacionMutation = useImportFinalizacion(materiaId);
  const [sinCorregir, setSinCorregir] = useState<TpsSinCorregirEntry[] | null>(null);
  const [finalizacionError, setFinalizacionError] = useState<string | null>(null);

  const handlePreview = (response: ImportPreviewResponse) => {
    setPreview(response);
    setState('previewing');
  };

  const handleImportSuccess = () => {
    setState('success');
  };

  const handleBack = () => {
    setPreview(null);
    setState('idle');
  };

  const handleFinalizacion = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setFinalizacionError(null);
    try {
      const result = await finalizacionMutation.mutateAsync(file);
      setSinCorregir(result.sin_corregir);
    } catch (err: unknown) {
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setFinalizacionError(err.response.data.detail);
      } else {
        setFinalizacionError('Error al procesar el reporte de finalización.');
      }
    }
    e.target.value = '';
  };

  if (state === 'previewing' && preview) {
    return (
      <ActivitySelector
        preview={preview}
        materiaId={materiaId}
        onSuccess={handleImportSuccess}
        onBack={handleBack}
      />
    );
  }

  if (state === 'error') {
    return (
      <div className="space-y-4">
        <GradeUploader onPreview={handlePreview} />
        <div className="rounded-md bg-danger-50 p-3 text-sm text-danger-600">
          Error al importar. Intentá de nuevo.
        </div>
        <Button variant="outline" onClick={handleBack}>
          Reintentar
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <Card>
        <CardHeader>
          <CardTitle>Importar calificaciones</CardTitle>
        </CardHeader>
        <CardContent>
          <GradeUploader onPreview={handlePreview} />
        </CardContent>
      </Card>

      {state === 'success' && (
        <Card>
          <CardHeader>
            <CardTitle>Reporte de finalización</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-neutral-600">
              Subí el reporte de finalización para detectar entregas sin corregir.
            </p>
            <input
              type="file"
              accept=".csv,.xlsx"
              onChange={handleFinalizacion}
              disabled={finalizacionMutation.isPending}
              className="block w-full text-sm file:mr-4 file:rounded-md file:border-0 file:px-4 file:py-2 file:text-sm file:bg-primary-50 file:text-primary-700 file:cursor-pointer hover:file:bg-primary-100"
            />
            {finalizacionMutation.isPending && (
              <div className="flex items-center gap-2 text-sm text-neutral-600">
                <Spinner size="sm" />
                <span>Procesando reporte...</span>
              </div>
            )}
            {finalizacionError && (
              <div className="rounded-md bg-danger-50 p-3 text-sm text-danger-600">
                {finalizacionError}
              </div>
            )}

            {sinCorregir !== null && (
              <div className="space-y-3">
                {sinCorregir.length > 0 ? (
                  <>
                    <p className="text-sm font-medium text-neutral-700">
                      Se detectaron {sinCorregir.length} entregas sin corregir
                    </p>
                    <div className="overflow-x-auto rounded-md border border-neutral-200">
                      <table className="min-w-full divide-y divide-neutral-200 text-sm">
                        <thead className="bg-neutral-50">
                          <tr>
                            <th className="px-3 py-2 text-left font-medium text-neutral-700">Alumno</th>
                            <th className="px-3 py-2 text-left font-medium text-neutral-700">Actividad</th>
                            <th className="px-3 py-2 text-left font-medium text-neutral-700">Fecha de entrega</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-neutral-200">
                          {sinCorregir.map((entry, i) => (
                            <tr key={i} className="hover:bg-neutral-50">
                              <td className="px-3 py-2">{entry.nombre}</td>
                              <td className="px-3 py-2">{entry.actividad}</td>
                              <td className="px-3 py-2 text-neutral-600">{entry.fecha_entrega}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => window.open(getTpsSinCorregirExportUrl(materiaId), '_blank')}
                    >
                      <Download className="mr-2 h-4 w-4" />
                      Exportar CSV
                    </Button>
                  </>
                ) : (
                  <p className="text-sm text-success-600">
                    No se detectaron entregas sin corregir
                  </p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
