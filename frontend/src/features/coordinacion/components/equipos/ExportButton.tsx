import { useState } from 'react';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import api from '@/shared/services/api';
import { getExportUrl } from '../../services/equipos.api';

export function ExportButton() {
  const [equipoId, setEquipoId] = useState('');
  const [equipoLabel, setEquipoLabel] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'error'; text: string } | null>(null);

  const handleExport = async () => {
    if (!equipoId) return;
    setIsLoading(true);
    setMessage(null);

    try {
      const url = getExportUrl(equipoId);
      const response = await api.get(url, { responseType: 'blob' });
      const blob = new Blob([response.data]);
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `equipo_${equipoLabel || equipoId}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(downloadUrl);
    } catch {
      setMessage({ type: 'error', text: 'Error al exportar. Intentá de nuevo.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Exportar CSV</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Input
          label="Equipo ID"
          value={equipoId}
          onChange={(e) => setEquipoId(e.target.value)}
          placeholder="Seleccioná un equipo para exportar"
        />
        <Input
          label="Nombre para el archivo"
          value={equipoLabel}
          onChange={(e) => setEquipoLabel(e.target.value)}
          placeholder="Ej: MATEMATICA_2025A"
        />

        {message && (
          <div className="rounded-md bg-danger-50 p-3 text-sm text-danger-600">
            {message.text}
          </div>
        )}

        <Button
          onClick={handleExport}
          isLoading={isLoading}
          disabled={!equipoId || isLoading}
        >
          {isLoading ? 'Exportando...' : 'Exportar CSV'}
        </Button>
        {!equipoId && (
          <p className="text-xs text-neutral-500">Seleccioná un equipo para exportar</p>
        )}
      </CardContent>
    </Card>
  );
}
