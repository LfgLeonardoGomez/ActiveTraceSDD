import { useState, useId, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Spinner } from '@/shared/components/ui/Spinner';
import { useMisTareas, useActualizarEstadoTarea } from '../../hooks/useTareas';
import { TareaStatusBadge } from './TareaStatusBadge';
import { TareaCommentThread } from './TareaCommentThread';
import type { Tarea, TareaEstado } from '../../types/tareas.types';

function isOverdue(tarea: Tarea): boolean {
  if (!tarea.fecha_limite) return false;
  return new Date(tarea.fecha_limite) < new Date() && tarea.estado !== 'aprobada';
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString();
}

export function TareaCard() {
  const cardId = useId();
  const { data: tareas, isLoading, isError, refetch } = useMisTareas();

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={`${cardId}-skeleton-${i}`} className="animate-pulse rounded-lg border border-neutral-200 bg-white p-6">
            <div className="mb-3 h-4 w-3/4 rounded bg-neutral-200" />
            <div className="mb-2 h-3 w-1/2 rounded bg-neutral-100" />
            <div className="mb-2 h-3 w-2/3 rounded bg-neutral-100" />
            <div className="mb-2 h-3 w-1/3 rounded bg-neutral-100" />
            <div className="h-3 w-1/4 rounded bg-neutral-100" />
          </div>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-danger-200 bg-danger-50 p-6 text-center">
        <p className="text-danger-600">Error al cargar tus tareas</p>
        <button
          onClick={() => refetch()}
          className="mt-2 text-sm font-medium text-primary-600 hover:underline"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!tareas || tareas.length === 0) {
    return (
      <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-6 text-center">
        <p className="text-neutral-600">No tenés tareas asignadas</p>
        <p className="mt-1 text-sm text-neutral-500">Cuando te asignen una tarea, aparecerá acá</p>
      </div>
    );
  }

  const sorted = [...tareas].sort(
    (a, b) => new Date(b.fecha_creacion).getTime() - new Date(a.fecha_creacion).getTime(),
  );

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {sorted.map((tarea) => (
        <TareaCardItem key={tarea.id} tarea={tarea} />
      ))}
    </div>
  );
}

function TareaCardItem({ tarea }: { tarea: Tarea }) {
  const [showComment, setShowComment] = useState(false);
  const actualizarEstado = useActualizarEstadoTarea();

  const handleEstadoChange = (nuevo: TareaEstado) => {
    actualizarEstado.mutate({ id: tarea.id, estado: nuevo });
  };

  const overdue = isOverdue(tarea);

  return (
    <Card className={overdue ? 'border-red-300' : undefined}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-base">{tarea.titulo}</CardTitle>
          <TareaStatusBadge
            estado={tarea.estado}
            canChange
            onEstadoChange={handleEstadoChange}
          />
        </div>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        {tarea.materia && (
          <div className="flex justify-between">
            <span className="text-neutral-500">Materia</span>
            <span className="font-medium text-neutral-900">{tarea.materia}</span>
          </div>
        )}
        <div className="flex justify-between">
          <span className="text-neutral-500">Asignador</span>
          <span className="font-medium text-neutral-900">{tarea.asignador}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-neutral-500">Creada</span>
          <span className="text-neutral-700">{formatDate(tarea.fecha_creacion)}</span>
        </div>
        {tarea.fecha_limite && (
          <div className="flex justify-between">
            <span className="text-neutral-500">Fecha límite</span>
            <span className={`font-medium ${overdue ? 'text-red-600' : 'text-neutral-900'}`}>
              {formatDate(tarea.fecha_limite)}
              {overdue && (
                <span title="Vencida" className="ml-1.5 rounded bg-red-100 px-1.5 py-0.5 text-xs text-red-700">
                  Vencida
                </span>
              )}
            </span>
          </div>
        )}

        {tarea.estado === 'pendiente' && (
          <button
            type="button"
            onClick={() => handleEstadoChange('en_proceso')}
            disabled={actualizarEstado.isPending}
            className="w-full rounded-md bg-blue-50 px-3 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-100 disabled:opacity-50"
          >
            Tomar en proceso
          </button>
        )}

        {(tarea.estado === 'en_proceso' || tarea.estado === 'completada') && (
          <button
            type="button"
            onClick={() => setShowComment(!showComment)}
            className="w-full rounded-md bg-green-50 px-3 py-1.5 text-xs font-medium text-green-700 hover:bg-green-100"
          >
            {tarea.estado === 'completada' ? 'Ver comentarios' : 'Completar'}
          </button>
        )}

        {showComment && (
          <TareaCommentThread
            comentarios={tarea.comentarios}
            onSendComment={
              tarea.estado === 'en_proceso'
                ? (contenido) => actualizarEstado.mutate({ id: tarea.id, estado: 'completada', comentario: contenido })
                : undefined
            }
            collapsed={false}
          />
        )}
      </CardContent>
    </Card>
  );
}
