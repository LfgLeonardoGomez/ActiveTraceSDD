import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Spinner } from '@/shared/components/ui/Spinner';
import { Button } from '@/shared/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { useConvocatoriaDetail, useConvocatorias } from '../../hooks/useColoquios';
import { ImportarAlumnosUploader } from './ImportarAlumnosUploader';

export function ConvocatoriaDetail() {
  const { convocatoriaId } = useParams<{ convocatoriaId: string }>();
  const navigate = useNavigate();
  const [showImport, setShowImport] = useState(false);

  const { data: convocatoria, isLoading, isError, refetch } = useConvocatoriaDetail(convocatoriaId ?? '');
  const { data: convocatorias } = useConvocatorias();

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Spinner size="lg" />
      </div>
    );
  }

  if (isError || !convocatoria) {
    return (
      <div className="rounded-lg border border-danger-200 bg-danger-50 p-6 text-center">
        <p className="text-danger-600">Error al cargar la convocatoria</p>
        <button
          onClick={() => refetch()}
          className="mt-2 text-sm font-medium text-primary-600 hover:underline"
        >
          Reintentar
        </button>
        <button
          onClick={() => navigate('/coordinacion/coloquios')}
          className="ml-4 text-sm font-medium text-neutral-600 hover:underline"
        >
          Volver
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={() => navigate('/coordinacion/coloquios')}
            className="mb-2 text-sm text-neutral-500 hover:text-neutral-700"
          >
            ← Volver a coloquios
          </button>
          <h2 className="text-lg font-semibold text-neutral-900">{convocatoria.titulo}</h2>
        </div>
        <Button onClick={() => setShowImport(!showImport)} variant="outline">
          Importar alumnos
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Información de la convocatoria</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1">
              <p className="text-sm text-neutral-500">Materia</p>
              <p className="font-medium text-neutral-900">{convocatoria.materia}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-neutral-500">Cohorte</p>
              <p className="font-medium text-neutral-900">{convocatoria.cohorte}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-neutral-500">Instancia</p>
              <p className="font-medium text-neutral-900">{convocatoria.instancia}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-neutral-500">Estado</p>
              <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                convocatoria.estado === 'activa' ? 'bg-success-100 text-success-700' : 'bg-neutral-100 text-neutral-600'
              }`}>
                {convocatoria.estado}
              </span>
            </div>
          </div>

          <div className="mt-4">
            <p className="mb-2 text-sm font-medium text-neutral-700">Días disponibles</p>
            <div className="space-y-2">
              {convocatoria.dias?.map((d, i) => (
                <div key={i} className="flex items-center justify-between rounded-md bg-neutral-50 px-3 py-2 text-sm">
                  <span className="text-neutral-900">{d.fecha}</span>
                  <span className="text-neutral-500">Cupo: {d.cupo_maximo}</span>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-neutral-500">Convocados</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-neutral-900">{convocatoria.total_convocados}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-neutral-500">Reservas activas</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-neutral-900">{convocatoria.reservas_activas}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-neutral-500">Cupos libres</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-neutral-900">{convocatoria.cupos_libres}</p>
          </CardContent>
        </Card>
      </div>

      {showImport && (
        <ImportarAlumnosUploader
          convocatorias={convocatorias ?? []}
          defaultConvocatoriaId={convocatoria.id}
        />
      )}
    </div>
  );
}
