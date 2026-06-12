import { useState, useEffect } from 'react';
import { Button } from '@/shared/components/ui/Button';
import { Spinner } from '@/shared/components/ui/Spinner';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { useUmbral, useUmbralMutation } from '../hooks/useUmbral';
import { useId } from 'react';

interface ThresholdEditorProps {
  materiaId: string;
}

export function ThresholdEditor({ materiaId }: ThresholdEditorProps) {
  const sliderId = useId();
  const inputId = useId();
  const { data: umbral, isLoading, isError, refetch } = useUmbral(materiaId);
  const mutation = useUmbralMutation(materiaId);

  const [localValue, setLocalValue] = useState<number>(60);
  const [originalValue, setOriginalValue] = useState<number>(60);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const hasChanges = localValue !== originalValue;

  useEffect(() => {
    if (umbral?.umbral_pct !== undefined) {
      setLocalValue(umbral.umbral_pct);
      setOriginalValue(umbral.umbral_pct);
    }
  }, [umbral]);

  const handleSave = async () => {
    setMessage(null);
    try {
      await mutation.mutateAsync(localValue);
      setOriginalValue(localValue);
      setMessage({ type: 'success', text: `Umbral actualizado a ${localValue}%` });
    } catch {
      setMessage({ type: 'error', text: 'Error al guardar el umbral. Intentá de nuevo.' });
    }
  };

  const handleCancel = () => {
    setLocalValue(originalValue);
    setMessage(null);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-danger-200 bg-danger-50 p-6 text-center">
        <p className="text-danger-600">Error al cargar el umbral</p>
        <button
          onClick={() => refetch()}
          className="mt-2 text-sm font-medium text-primary-600 hover:underline"
        >
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Configurar umbral de aprobación</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex items-center gap-4">
          <input
            id={sliderId}
            type="range"
            min={0}
            max={100}
            value={localValue}
            onChange={(e) => setLocalValue(Number(e.target.value))}
            className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-neutral-200 accent-primary-600"
          />
          <div className="flex items-center gap-2">
            <input
              id={inputId}
              type="number"
              min={0}
              max={100}
              value={localValue}
              onChange={(e) => setLocalValue(Math.min(100, Math.max(0, Number(e.target.value))))}
              className="w-16 rounded-md border border-neutral-300 px-2 py-1 text-center text-sm"
            />
            <span className="text-sm font-medium text-neutral-700">%</span>
          </div>
        </div>

        <div className="text-center">
          <span className="text-2xl font-bold text-primary-600">{localValue}%</span>
        </div>

        {message && (
          <div
            className={`rounded-md p-3 text-sm ${
              message.type === 'success'
                ? 'bg-success-50 text-success-600'
                : 'bg-danger-50 text-danger-600'
            }`}
          >
            {message.text}
          </div>
        )}

        <div className="flex gap-3">
          <Button onClick={handleSave} disabled={!hasChanges || mutation.isPending}>
            {mutation.isPending ? 'Guardando...' : 'Guardar'}
          </Button>
          {hasChanges && (
            <Button variant="outline" onClick={handleCancel}>
              Cancelar
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
