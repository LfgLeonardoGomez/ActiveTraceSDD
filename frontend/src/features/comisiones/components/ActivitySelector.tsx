import { useState } from 'react';
import { Button } from '@/shared/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { useImportConfirm } from '../hooks/useCalificaciones';
import type { ImportPreviewResponse } from '../types/comisiones.types';
import { Check, ChevronDown, ChevronUp } from 'lucide-react';

interface ActivitySelectorProps {
  preview: ImportPreviewResponse;
  materiaId: string;
  onSuccess: () => void;
  onBack: () => void;
}

export function ActivitySelector({ preview, materiaId, onSuccess, onBack }: ActivitySelectorProps) {
  const [selected, setSelected] = useState<string[]>(
    preview.actividades.map((a) => a.id),
  );
  const [showErrors, setShowErrors] = useState(false);
  const confirmMutation = useImportConfirm(materiaId);
  const [result, setResult] = useState<{ imported_count: number; errors: { row: number; mensaje: string }[] } | null>(
    null,
  );

  const allSelected = selected.length === preview.actividades.length;

  const toggleAll = () => {
    if (allSelected) {
      setSelected([]);
    } else {
      setSelected(preview.actividades.map((a) => a.id));
    }
  };

  const toggle = (id: string) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  };

  const handleConfirm = async () => {
    try {
      const response = await confirmMutation.mutateAsync(selected);
      setResult({ imported_count: response.imported_count, errors: response.errors });
    } catch {
      // Error state handled by mutation state
    }
  };

  if (result) {
    const hasErrors = result.errors.length > 0;

    return (
      <Card>
        <CardHeader>
          <CardTitle>
            {hasErrors
              ? `${result.imported_count} calificaciones importadas`
              : `${result.imported_count} calificaciones importadas correctamente`}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2 text-sm text-success-600">
            <Check className="h-5 w-5" />
            <span>{result.imported_count} calificaciones importadas correctamente</span>
          </div>

          {hasErrors && (
            <div>
              <button
                onClick={() => setShowErrors(!showErrors)}
                className="flex items-center gap-1 text-sm text-warning-600 hover:underline"
              >
                {showErrors ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                {result.errors.length} error(es) — {showErrors ? 'ocultar' : 'ver detalles'}
              </button>
              {showErrors && (
                <div className="mt-2 max-h-40 space-y-1 overflow-y-auto rounded-md bg-danger-50 p-3">
                  {result.errors.map((err, i) => (
                    <p key={i} className="text-xs text-danger-600">
                      Fila {err.row}: {err.mensaje}
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="flex gap-3">
            <Button variant="outline" onClick={onSuccess}>
              Ver análisis
            </Button>
            <Button variant="outline" onClick={onBack}>
              Importar más datos
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Vista previa de importación</CardTitle>
        <p className="text-sm text-muted-foreground">
          Se detectaron {preview.actividades.length} actividades y {preview.alumnos.length} alumnos
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="overflow-x-auto rounded-md border border-neutral-200">
          <table className="min-w-full divide-y divide-neutral-200 text-sm">
            <thead className="bg-neutral-50">
              <tr>
                <th className="px-3 py-2 text-left">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={toggleAll}
                    className="rounded border-neutral-300"
                  />
                </th>
                <th className="px-3 py-2 text-left font-medium text-neutral-700">Actividad</th>
                <th className="px-3 py-2 text-left font-medium text-neutral-700">Tipo</th>
                <th className="px-3 py-2 text-left font-medium text-neutral-700">Muestras</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-200">
              {preview.actividades.map((act) => {
                const samples = preview.alumnos
                  .slice(0, 3)
                  .map((a) => `${a.nombre}: ${a.notas_detectadas}`)
                  .join(', ');

                return (
                  <tr key={act.id} className="hover:bg-neutral-50">
                    <td className="px-3 py-2">
                      <input
                        type="checkbox"
                        checked={selected.includes(act.id)}
                        onChange={() => toggle(act.id)}
                        className="rounded border-neutral-300"
                      />
                    </td>
                    <td className="px-3 py-2 font-medium">{act.nombre}</td>
                    <td className="px-3 py-2 text-neutral-600">{act.tipo}</td>
                    <td className="px-3 py-2 text-xs text-neutral-500">
                      {samples || '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {selected.length === 0 && (
          <p className="text-sm text-warning-600">
            Seleccioná al menos una actividad para importar
          </p>
        )}

        {confirmMutation.isError && (
          <div className="rounded-md bg-danger-50 p-3 text-sm text-danger-600">
            Error al importar. Intentá de nuevo.
          </div>
        )}

        <div className="flex gap-3">
          <Button
            onClick={handleConfirm}
            disabled={selected.length === 0 || confirmMutation.isPending}
          >
            {confirmMutation.isPending
              ? 'Importando...'
              : `Confirmar importación (${selected.length})`}
          </Button>
          <Button variant="outline" onClick={onBack}>
            Volver
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
