import { useId, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Spinner } from '@/shared/components/ui/Spinner';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/shared/components/ui/Card';
import { Button } from '@/shared/components/ui/Button';
import { useAvisos } from '../../hooks/useAvisos';
import type { Aviso } from '../../types/avisos.types';

type FilterEstado = string | undefined;
type FilterSeveridad = string | undefined;
type FilterAlcance = string | undefined;

const SEVERIDAD_COLORS: Record<string, string> = {
  informativo: 'bg-blue-100 text-blue-800',
  advertencia: 'bg-amber-100 text-amber-800',
  critico: 'bg-red-100 text-red-800',
};

const ESTADO_COLORS: Record<string, string> = {
  borrador: 'bg-neutral-100 text-neutral-600',
  publicado: 'bg-green-100 text-green-800',
  vencido: 'bg-neutral-100 text-neutral-400',
};

export function AvisoCard() {
  const cardId = useId();
  const navigate = useNavigate();
  const [estado, setEstado] = useState<FilterEstado>(undefined);
  const [severidad, setSeveridad] = useState<FilterSeveridad>(undefined);
  const [alcance, setAlcance] = useState<FilterAlcance>(undefined);

  const filters: Record<string, string> = {};
  if (estado) filters.estado = estado;
  if (severidad) filters.severidad = severidad;
  if (alcance) filters.alcance = alcance;

  const { data: avisos, isLoading, isError, refetch } = useAvisos(Object.keys(filters).length > 0 ? filters : undefined);

  if (isLoading) {
    return (
      <div className="grid gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={`${cardId}-skeleton-${i}`} className="animate-pulse rounded-lg border border-neutral-200 bg-white p-6">
            <div className="mb-3 h-5 w-2/3 rounded bg-neutral-200" />
            <div className="mb-2 h-3 w-1/3 rounded bg-neutral-100" />
            <div className="h-3 w-1/2 rounded bg-neutral-100" />
          </div>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-danger-200 bg-danger-50 p-6 text-center">
        <p className="text-danger-600">Error al cargar avisos</p>
        <Button onClick={() => refetch()} variant="link" className="mt-2">
          Reintentar
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex flex-wrap gap-2">
          <select
            aria-label="Filtrar por estado"
            value={estado ?? ''}
            onChange={(e) => setEstado(e.target.value || undefined)}
            className="h-9 rounded-md border border-neutral-300 bg-white px-3 text-sm"
          >
            <option value="">Todos los estados</option>
            <option value="borrador">Borrador</option>
            <option value="publicado">Publicado</option>
            <option value="vencido">Vencido</option>
          </select>
          <select
            aria-label="Filtrar por severidad"
            value={severidad ?? ''}
            onChange={(e) => setSeveridad(e.target.value || undefined)}
            className="h-9 rounded-md border border-neutral-300 bg-white px-3 text-sm"
          >
            <option value="">Todas las severidades</option>
            <option value="informativo">Informativo</option>
            <option value="advertencia">Advertencia</option>
            <option value="critico">Crítico</option>
          </select>
          <select
            aria-label="Filtrar por alcance"
            value={alcance ?? ''}
            onChange={(e) => setAlcance(e.target.value || undefined)}
            className="h-9 rounded-md border border-neutral-300 bg-white px-3 text-sm"
          >
            <option value="">Todos los alcances</option>
            <option value="global">Global</option>
            <option value="materia">Materia</option>
            <option value="cohorte">Cohorte</option>
          </select>
        </div>
        <Button onClick={() => navigate('/coordinacion/avisos/nuevo')}>
          + Nuevo aviso
        </Button>
      </div>

      {!avisos || avisos.length === 0 ? (
        <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-6 text-center">
          <p className="text-neutral-600">No hay avisos publicados</p>
          <Button onClick={() => navigate('/coordinacion/avisos/nuevo')} variant="link" className="mt-2">
            + Nuevo aviso
          </Button>
        </div>
      ) : (
        <div className="grid gap-4">
          {[...avisos]
            .sort((a, b) => new Date(b.creado).getTime() - new Date(a.creado).getTime())
            .map((aviso) => (
              <AvisoCardItem key={aviso.id} aviso={aviso} />
            ))}
        </div>
      )}
    </div>
  );
}

function AvisoCardItem({ aviso }: { aviso: Aviso }) {
  return (
    <Card
      className={`cursor-pointer transition-shadow hover:shadow-md ${
        aviso.severidad === 'critico' && aviso.estado === 'publicado'
          ? 'border-l-4 border-l-red-500'
          : ''
      }`}
      onClick={() => navigate(`/coordinacion/avisos/${aviso.id}/editar`)}
    >
      <CardHeader className="flex-row items-start justify-between gap-4">
        <div className="space-y-1">
          <CardTitle className="text-base">{aviso.titulo}</CardTitle>
          <CardDescription>
            {aviso.alcance === 'global'
              ? 'Global'
              : aviso.alcance === 'materia'
                ? `Materia: ${aviso.materia_id ?? '—'}`
                : `Cohorte: ${aviso.cohorte_id ?? '—'}`}
          </CardDescription>
        </div>
        <div className="flex flex-wrap gap-2 shrink-0">
          <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${SEVERIDAD_COLORS[aviso.severidad] ?? 'bg-neutral-100 text-neutral-700'}`}>
            {aviso.severidad}
          </span>
          <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${ESTADO_COLORS[aviso.estado] ?? 'bg-neutral-100 text-neutral-600'}`}>
            {aviso.estado}
          </span>
        </div>
      </CardHeader>
      <CardContent className="text-sm space-y-2">
        <div className="line-clamp-2 text-neutral-700">{aviso.cuerpo}</div>
        <div className="flex flex-wrap gap-4 text-neutral-500">
          {aviso.fecha_desde && (
            <span>Desde: {new Date(aviso.fecha_desde).toLocaleDateString()}</span>
          )}
          {aviso.fecha_hasta ? (
            <span>Hasta: {new Date(aviso.fecha_hasta).toLocaleDateString()}</span>
          ) : (
            <span>Sin vencimiento</span>
          )}
          <span>Requiere ack: {aviso.requiere_ack ? 'Sí' : 'No'}</span>
        </div>
      </CardContent>
      {aviso.requiere_ack && (
        <CardFooter className="text-xs text-neutral-500">
          {aviso.leidos ?? 0}/{aviso.total_destinatarios ?? 0} destinatarios leyeron
        </CardFooter>
      )}
    </Card>
  );
}
