import { useState } from 'react';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Spinner } from '@/shared/components/ui/Spinner';
import { useContenidoAula } from '../../hooks/useEncuentros';

export function ContenidoAulaPreview() {
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [ready, setReady] = useState(false);
  const [copied, setCopied] = useState(false);

  const { data, isLoading, isError, refetch } = useContenidoAula(ready ? filters : undefined);

  const handleGenerate = () => {
    setReady(true);
  };

  const handleCopy = async () => {
    const text = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formattedContent = (() => {
    if (!data) return '';
    if (typeof data === 'string') return data;
    if (Array.isArray(data)) {
      return data
        .map(
          (item: Record<string, unknown>) =>
            `<tr><td>${String(item.materia ?? '')}</td><td>${String(item.fecha ?? '')}</td><td>${String(item.hora ?? '')}</td><td>${String(item.titulo ?? '')}</td><td>${String(item.docente ?? '')}</td><td><a href="${String(item.enlace ?? '')}">${String(item.enlace ?? '')}</a></td></tr>`,
        )
        .join('\n');
    }
    return JSON.stringify(data, null, 2);
  })();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Contenido para el Aula Virtual</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-3">
          <Input
            placeholder="Materia ID"
            className="w-48"
            value={filters.materia_id ?? ''}
            onChange={(e) => setFilters((f) => ({ ...f, materia_id: e.target.value }))}
          />
          <Input
            placeholder="Cohorte ID"
            className="w-48"
            value={filters.cohorte_id ?? ''}
            onChange={(e) => setFilters((f) => ({ ...f, cohorte_id: e.target.value }))}
          />
          <Input
            type="date"
            className="w-44"
            value={filters.fecha_desde ?? ''}
            onChange={(e) => setFilters((f) => ({ ...f, fecha_desde: e.target.value }))}
          />
          <Input
            type="date"
            className="w-44"
            value={filters.fecha_hasta ?? ''}
            onChange={(e) => setFilters((f) => ({ ...f, fecha_hasta: e.target.value }))}
          />
          <Button onClick={handleGenerate} disabled={isLoading}>
            {isLoading ? 'Generando...' : 'Generar'}
          </Button>
        </div>

        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <Spinner size="lg" />
          </div>
        )}

        {isError && (
          <div className="rounded-lg border border-danger-200 bg-danger-50 p-6 text-center">
            <p className="text-danger-600">Error al generar contenido</p>
            <button onClick={() => refetch()} className="mt-2 text-sm font-medium text-primary-600 hover:underline">
              Reintentar
            </button>
          </div>
        )}

        {!isLoading && !isError && ready && !data && (
          <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-6 text-center">
            <p className="text-neutral-600">No hay encuentros programados en el período</p>
          </div>
        )}

        {formattedContent && (
          <div className="space-y-3">
            <div className="overflow-x-auto rounded-md border border-neutral-200 bg-neutral-50 p-4">
              {Array.isArray(data) ? (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-neutral-200 text-left">
                      <th className="pb-2 pr-4 font-medium text-neutral-600">Materia</th>
                      <th className="pb-2 pr-4 font-medium text-neutral-600">Fecha</th>
                      <th className="pb-2 pr-4 font-medium text-neutral-600">Hora</th>
                      <th className="pb-2 pr-4 font-medium text-neutral-600">Título</th>
                      <th className="pb-2 pr-4 font-medium text-neutral-600">Docente</th>
                      <th className="pb-2 font-medium text-neutral-600">Enlace</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data as Record<string, unknown>[]).map((item, i) => (
                      <tr key={i} className="border-b border-neutral-100">
                        <td className="py-2 pr-4 text-neutral-900">{String(item.materia ?? '')}</td>
                        <td className="py-2 pr-4 text-neutral-600">{String(item.fecha ?? '')}</td>
                        <td className="py-2 pr-4 text-neutral-600">{String(item.hora ?? '')}</td>
                        <td className="py-2 pr-4 text-neutral-900">{String(item.titulo ?? '')}</td>
                        <td className="py-2 pr-4 text-neutral-600">{String(item.docente ?? '')}</td>
                        <td className="py-2">
                          <a href={String(item.enlace ?? '')} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">Abrir</a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <pre className="whitespace-pre-wrap text-sm text-neutral-700">
                  {typeof data === 'string' ? data : JSON.stringify(data, null, 2)}
                </pre>
              )}
            </div>
            <Button variant="outline" onClick={handleCopy}>
              {copied ? '¡Copiado!' : 'Copiar al portapapeles'}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
