import { useNavigate } from 'react-router-dom';
import { usePermissions } from '@/shared/hooks/usePermissions';
import { Users, BookOpen, Calendar, ClipboardCheck, Megaphone, Activity } from 'lucide-react';

interface KpiCard {
  label: string;
  value: string;
  icon: React.ReactNode;
  to?: string;
}

interface QuickAction {
  label: string;
  description: string;
  to: string;
  permission?: string;
  icon: React.ReactNode;
}

const KPI_CARDS: KpiCard[] = [
  { label: 'Equipos activos', value: '—', icon: <Users className="size-6" />, to: '/coordinacion/equipos' },
  { label: 'Próximos encuentros', value: '—', icon: <Calendar className="size-6" />, to: '/coordinacion/encuentros' },
  { label: 'Tareas pendientes', value: '—', icon: <ClipboardCheck className="size-6" />, to: '/coordinacion/tareas' },
  { label: 'Avisos activos', value: '—', icon: <Megaphone className="size-6" />, to: '/coordinacion/avisos' },
  { label: 'Coloquios activos', value: '—', icon: <Activity className="size-6" />, to: '/coordinacion/coloquios' },
  { label: 'Carreras activas', value: '—', icon: <BookOpen className="size-6" />, to: '/coordinacion/estructura' },
];

const QUICK_ACTIONS: QuickAction[] = [
  {
    label: 'Nuevo aviso',
    description: 'Crear un aviso para destinatarios específicos',
    to: '/coordinacion/avisos/nuevo',
    permission: 'avisos:crear',
    icon: <Megaphone className="size-5" />,
  },
  {
    label: 'Asignar tarea',
    description: 'Asignar una tarea a un docente',
    to: '/coordinacion/tareas/asignar',
    permission: 'tareas:asignar',
    icon: <ClipboardCheck className="size-5" />,
  },
  {
    label: 'Registrar guardia',
    description: 'Registrar una guardia de tutoría',
    to: '/coordinacion/encuentros/guardias',
    permission: 'encuentros:registrar',
    icon: <Calendar className="size-5" />,
  },
  {
    label: 'Crear equipo',
    description: 'Asignar docentes a una comisión',
    to: '/coordinacion/equipos',
    permission: 'equipos:crear',
    icon: <Users className="size-5" />,
  },
];

export default function CoordinacionHome() {
  const navigate = useNavigate();
  const { can } = usePermissions();

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-neutral-900">Panel de Coordinación</h1>
        <p className="mt-1 text-sm text-neutral-500">Resumen general de actividades académicas</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {KPI_CARDS.map((kpi) => (
          <button
            key={kpi.label}
            onClick={() => kpi.to && navigate(kpi.to)}
            className="flex flex-col gap-2 rounded-lg border border-neutral-200 bg-white p-4 text-left transition-colors hover:border-primary-300 hover:shadow-sm"
          >
            <div className="text-neutral-400">{kpi.icon}</div>
            <span className="text-2xl font-bold text-neutral-900">{kpi.value}</span>
            <span className="text-xs text-neutral-500">{kpi.label}</span>
          </button>
        ))}
      </div>

      <div>
        <h2 className="text-lg font-semibold text-neutral-900">Acciones rápidas</h2>
        <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {QUICK_ACTIONS.filter((action) => !action.permission || can(action.permission)).map((action) => (
            <button
              key={action.label}
              onClick={() => navigate(action.to)}
              className="flex items-start gap-3 rounded-lg border border-neutral-200 bg-white p-4 text-left transition-colors hover:border-primary-300 hover:shadow-sm"
            >
              <div className="mt-0.5 text-primary-600">{action.icon}</div>
              <div>
                <span className="text-sm font-medium text-neutral-900">{action.label}</span>
                <p className="text-xs text-neutral-500">{action.description}</p>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
