import { useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { useCarreras, useCohortes, useEvaluaciones } from '../hooks/useEstructura';
import { CarreraForm } from '../components/estructura/CarreraForm';
import { CohorteForm } from '../components/estructura/CohorteForm';
import { ProgramaUploader } from '../components/estructura/ProgramaUploader';
import { EvaluacionForm } from '../components/estructura/EvaluacionForm';
import { EvaluacionCalendar } from '../components/estructura/EvaluacionCalendar';
import { Spinner } from '@/shared/components/ui/Spinner';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import type { Carrera, Cohorte } from '../types/estructura.types';

const SUB_ROUTES = [
  { label: 'Carreras', path: '/coordinacion/estructura', end: true },
  { label: 'Cohortes', path: '/coordinacion/estructura/cohortes' },
  { label: 'Programas', path: '/coordinacion/estructura/programas' },
  { label: 'Evaluaciones', path: '/coordinacion/estructura/evaluaciones' },
] as const;

export function EstructuraLayout() {
  const location = useLocation();

  return (
    <div className="flex flex-col gap-6">
      <nav className="flex overflow-x-auto border-b border-neutral-200">
        {SUB_ROUTES.map((route) => (
          <NavLink
            key={route.path}
            to={route.path}
            end={'end' in route ? route.end : false}
            className={({ isActive }) =>
              cn(
                'whitespace-nowrap px-4 py-3 text-sm font-medium transition-colors',
                isActive
                  ? 'border-b-2 border-primary-600 text-primary-600'
                  : 'text-neutral-600 hover:text-neutral-900',
              )
            }
          >
            {route.label}
          </NavLink>
        ))}
      </nav>

      <div className="flex-1">
        {location.pathname === '/coordinacion/estructura' && <CarrerasView />}
        {location.pathname === '/coordinacion/estructura/cohortes' && <CohortesView />}
        {location.pathname === '/coordinacion/estructura/programas' && <ProgramasView />}
        {location.pathname === '/coordinacion/estructura/evaluaciones' && <EvaluacionesView />}
      </div>
    </div>
  );
}

function CarrerasView() {
  const { data: carreras, isLoading, isError, refetch } = useCarreras();
  const [editingCarrera, setEditingCarrera] = useState<Carrera | null>(null);
  const [showForm, setShowForm] = useState(false);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-neutral-900">Carreras</h2>
        {!showForm && (
          <button
            onClick={() => { setShowForm(true); setEditingCarrera(null); }}
            className="rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
          >
            + Nueva carrera
          </button>
        )}
      </div>

      {showForm && (
        <CarreraForm
          carrera={editingCarrera}
          onSuccess={() => { setShowForm(false); setEditingCarrera(null); }}
        />
      )}

      {isLoading ? (
        <div className="flex justify-center py-8">
          <Spinner size="lg" />
        </div>
      ) : isError ? (
        <div className="rounded-lg border border-danger-200 bg-danger-50 p-6 text-center">
          <p className="text-danger-600">Error al cargar carreras</p>
          <button onClick={() => refetch()} className="mt-2 text-sm font-medium text-primary-600 hover:underline">
            Reintentar
          </button>
        </div>
      ) : !carreras || carreras.length === 0 ? (
        <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-6 text-center">
          <p className="text-neutral-600">No hay carreras registradas</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {carreras.map((c) => (
            <Card key={c.id}>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">{c.nombre}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Código</span>
                    <span className="font-medium text-neutral-900">{c.codigo}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Estado</span>
                    <span className={`font-medium ${c.activa ? 'text-success-600' : 'text-neutral-600'}`}>
                      {c.activa ? 'Activa' : 'Inactiva'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Creada</span>
                    <span className="text-neutral-600">{new Date(c.creada).toLocaleDateString()}</span>
                  </div>
                </div>
                <button
                  onClick={() => { setEditingCarrera(c); setShowForm(true); }}
                  className="mt-3 text-sm font-medium text-primary-600 hover:underline"
                >
                  Editar
                </button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function CohortesView() {
  const { data: cohortes, isLoading, isError, refetch } = useCohortes();
  const [editingCohorte, setEditingCohorte] = useState<Cohorte | null>(null);
  const [showForm, setShowForm] = useState(false);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-neutral-900">Cohortes</h2>
        {!showForm && (
          <button
            onClick={() => { setShowForm(true); setEditingCohorte(null); }}
            className="rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
          >
            + Nuevo cohorte
          </button>
        )}
      </div>

      {showForm && (
        <CohorteForm
          cohorte={editingCohorte}
          onSuccess={() => { setShowForm(false); setEditingCohorte(null); }}
        />
      )}

      {isLoading ? (
        <div className="flex justify-center py-8">
          <Spinner size="lg" />
        </div>
      ) : isError ? (
        <div className="rounded-lg border border-danger-200 bg-danger-50 p-6 text-center">
          <p className="text-danger-600">Error al cargar cohortes</p>
          <button onClick={() => refetch()} className="mt-2 text-sm font-medium text-primary-600 hover:underline">
            Reintentar
          </button>
        </div>
      ) : !cohortes || cohortes.length === 0 ? (
        <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-6 text-center">
          <p className="text-neutral-600">No hay cohortes registrados</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cohortes.map((c) => (
            <Card key={c.id}>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">{c.nombre} {c.year}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Desde</span>
                    <span className="text-neutral-900">{new Date(c.fecha_desde).toLocaleDateString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Hasta</span>
                    <span className="text-neutral-900">{new Date(c.fecha_hasta).toLocaleDateString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Estado</span>
                    <span className={`font-medium ${c.estado === 'activo' ? 'text-success-600' : 'text-neutral-600'}`}>
                      {c.estado === 'activo' ? 'Activo' : 'Inactivo'}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => { setEditingCohorte(c); setShowForm(true); }}
                  className="mt-3 text-sm font-medium text-primary-600 hover:underline"
                >
                  Editar
                </button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function ProgramasView() {
  return <ProgramaUploader />;
}

function EvaluacionesView() {
  const [view, setView] = useState<'lista' | 'calendario'>('lista');
  const { data: evaluaciones, isLoading, isError, refetch } = useEvaluaciones();
  const [editingEvaluacion, setEditingEvaluacion] = useState<null | any>(null);
  const [showForm, setShowForm] = useState(false);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-neutral-900">Evaluaciones</h2>
        <div className="flex items-center gap-2">
          <div className="flex overflow-hidden rounded-md border border-neutral-300">
            <button
              onClick={() => setView('lista')}
              className={`px-3 py-1.5 text-sm font-medium ${
                view === 'lista' ? 'bg-primary-600 text-white' : 'bg-white text-neutral-600 hover:bg-neutral-50'
              }`}
            >
              Lista
            </button>
            <button
              onClick={() => setView('calendario')}
              className={`px-3 py-1.5 text-sm font-medium ${
                view === 'calendario' ? 'bg-primary-600 text-white' : 'bg-white text-neutral-600 hover:bg-neutral-50'
              }`}
            >
              Calendario
            </button>
          </div>
          {!showForm && view === 'lista' && (
            <button
              onClick={() => { setShowForm(true); setEditingEvaluacion(null); }}
              className="rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
            >
              + Nueva evaluación
            </button>
          )}
        </div>
      </div>

      {view === 'calendario' ? (
        <EvaluacionCalendar />
      ) : (
        <>
          {showForm && (
            <EvaluacionForm
              evaluacion={editingEvaluacion}
              onSuccess={() => { setShowForm(false); setEditingEvaluacion(null); }}
            />
          )}

          {isLoading ? (
            <div className="flex justify-center py-8">
              <Spinner size="lg" />
            </div>
          ) : isError ? (
            <div className="rounded-lg border border-danger-200 bg-danger-50 p-6 text-center">
              <p className="text-danger-600">Error al cargar evaluaciones</p>
              <button onClick={() => refetch()} className="mt-2 text-sm font-medium text-primary-600 hover:underline">
                Reintentar
              </button>
            </div>
          ) : !evaluaciones || evaluaciones.length === 0 ? (
            <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-6 text-center">
              <p className="text-neutral-600">No hay evaluaciones registradas</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-neutral-200 text-left">
                    <th className="pb-3 pr-4 font-medium text-neutral-600">Materia</th>
                    <th className="pb-3 pr-4 font-medium text-neutral-600">Tipo</th>
                    <th className="pb-3 pr-4 font-medium text-neutral-600">Instancia</th>
                    <th className="pb-3 pr-4 font-medium text-neutral-600">Título</th>
                    <th className="pb-3 pr-4 font-medium text-neutral-600">Fecha</th>
                    <th className="pb-3 font-medium text-neutral-600">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {evaluaciones.map((ev) => (
                    <tr key={ev.id} className="border-b border-neutral-100">
                      <td className="py-3 pr-4 text-neutral-900">{ev.materia}</td>
                      <td className="py-3 pr-4">
                        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          ev.tipo === 'parcial' ? 'bg-blue-100 text-blue-700' :
                          ev.tipo === 'tp' ? 'bg-green-100 text-green-700' :
                          'bg-purple-100 text-purple-700'
                        }`}>
                          {ev.tipo === 'parcial' ? 'Parcial' : ev.tipo === 'tp' ? 'TP' : 'Coloquio'}
                        </span>
                      </td>
                      <td className="py-3 pr-4 text-neutral-600">{ev.instancia}</td>
                      <td className="py-3 pr-4 text-neutral-900">{ev.titulo}</td>
                      <td className="py-3 pr-4 text-neutral-600">{new Date(ev.fecha).toLocaleDateString()}</td>
                      <td className="py-3">
                        <button
                          onClick={() => { setEditingEvaluacion(ev); setShowForm(true); }}
                          className="text-sm font-medium text-primary-600 hover:underline"
                        >
                          Editar
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export function EstructuraIndex() {
  return <CarrerasView />;
}
