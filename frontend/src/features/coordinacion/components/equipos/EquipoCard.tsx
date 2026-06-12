import { useId } from 'react';
import { useNavigate } from 'react-router-dom';
import { Spinner } from '@/shared/components/ui/Spinner';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Button } from '@/shared/components/ui/Button';
import { useAuth } from '@/shared/services/AuthContext';
import { useMisEquipos } from '../../hooks/useEquipos';
import type { Equipo } from '../../types/equipos.types';

export function EquipoCard() {
  const cardId = useId();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { data: equipos, isLoading, isError, refetch } = useMisEquipos();

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={`${cardId}-skeleton-${i}`} className="animate-pulse rounded-lg border border-neutral-200 bg-white p-6">
            <div className="mb-3 h-4 w-3/4 rounded bg-neutral-200" />
            <div className="mb-2 h-3 w-1/2 rounded bg-neutral-100" />
            <div className="mb-2 h-3 w-2/3 rounded bg-neutral-100" />
            <div className="h-3 w-1/3 rounded bg-neutral-100" />
          </div>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-danger-200 bg-danger-50 p-6 text-center">
        <p className="text-danger-600">Error al cargar tus equipos</p>
        <button
          onClick={() => refetch()}
          className="mt-2 text-sm font-medium text-primary-600 hover:underline"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!equipos || equipos.length === 0) {
    const esCoordinador = user?.roles?.some((r) => r.name === 'COORDINADOR' || r.name === 'ADMIN');
    return (
      <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-6 text-center">
        <p className="text-neutral-600">No tenés equipos asignados</p>
        {esCoordinador && (
          <Button onClick={() => navigate('/coordinacion/estructura')} variant="outline" className="mt-3">
            Ir a estructura
          </Button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-neutral-500">Mostrando {equipos.length} asignaciones</p>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {equipos.map((equipo) => (
          <EquipoCardItem key={equipo.id} equipo={equipo} />
        ))}
      </div>
    </div>
  );
}

function EquipoCardItem({ equipo }: { equipo: Equipo }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{equipo.materia}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-neutral-500">Carrera</span>
          <span className="font-medium text-neutral-900">{equipo.carrera}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-neutral-500">Cohorte</span>
          <span className="font-medium text-neutral-900">{equipo.cohorte}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-neutral-500">Roles</span>
          <span className="font-medium text-neutral-900">{equipo.roles.join(', ')}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-neutral-500">Vigencia</span>
          <span className="font-medium text-neutral-900">
            {equipo.vigencia_desde} — {equipo.vigencia_hasta}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-neutral-500">Estado</span>
          <span className={`font-medium ${equipo.estado === 'activo' ? 'text-success-600' : 'text-neutral-600'}`}>
            {equipo.estado}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
