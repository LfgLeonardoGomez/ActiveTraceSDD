import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Spinner } from '@/shared/components/ui/Spinner';
import { useEvaluaciones } from '../../hooks/useEstructura';
import type { Evaluacion } from '../../types/estructura.types';

const MONTHS = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
const DAYS = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];

const TIPO_LABELS: Record<string, string> = {
  parcial: 'Parcial',
  tp: 'TP',
  coloquio: 'Coloquio',
};

const TIPO_COLORS: Record<string, string> = {
  parcial: 'bg-blue-100 text-blue-700',
  tp: 'bg-green-100 text-green-700',
  coloquio: 'bg-purple-100 text-purple-700',
};

export function EvaluacionCalendar() {
  const { data: evaluaciones, isLoading, isError, refetch } = useEvaluaciones();
  const today = new Date();
  const [currentMonth, setCurrentMonth] = useState(today.getMonth());
  const [currentYear, setCurrentYear] = useState(today.getFullYear());
  const [selectedDay, setSelectedDay] = useState<number | null>(null);
  const [tooltipEvaluaciones, setTooltipEvaluaciones] = useState<Evaluacion[] | null>(null);

  const evalByDate = useMemo(() => {
    const map = new Map<string, Evaluacion[]>();
    if (evaluaciones) {
      for (const ev of evaluaciones) {
        const key = ev.fecha.split('T')[0];
        if (!map.has(key)) map.set(key, []);
        map.get(key)!.push(ev);
      }
    }
    return map;
  }, [evaluaciones]);

  const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
  const firstDayOfWeek = new Date(currentYear, currentMonth, 1).getDay();

  const prevMonth = () => {
    if (currentMonth === 0) {
      setCurrentMonth(11);
      setCurrentYear((y) => y - 1);
    } else {
      setCurrentMonth((m) => m - 1);
    }
    setSelectedDay(null);
    setTooltipEvaluaciones(null);
  };

  const nextMonth = () => {
    if (currentMonth === 11) {
      setCurrentMonth(0);
      setCurrentYear((y) => y + 1);
    } else {
      setCurrentMonth((m) => m + 1);
    }
    setSelectedDay(null);
    setTooltipEvaluaciones(null);
  };

  const handleDayClick = (day: number) => {
    const dateStr = formatDateKey(currentYear, currentMonth, day);
    const dayEvals = evalByDate.get(dateStr) ?? [];
    if (dayEvals.length > 0) {
      setSelectedDay(selectedDay === day ? null : day);
      setTooltipEvaluaciones(selectedDay === day ? null : dayEvals);
    }
  };

  const dates: { day: number; hasEval: boolean; isToday: boolean }[] = [];
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = formatDateKey(currentYear, currentMonth, d);
    dates.push({
      day: d,
      hasEval: evalByDate.has(dateStr),
      isToday:
        d === today.getDate() &&
        currentMonth === today.getMonth() &&
        currentYear === today.getFullYear(),
    });
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Spinner size="lg" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-danger-200 bg-danger-50 p-6 text-center">
        <p className="text-danger-600">Error al cargar evaluaciones</p>
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
        <div className="flex items-center justify-between">
          <CardTitle>Calendario de Evaluaciones</CardTitle>
          <div className="flex items-center gap-2">
            <button
              onClick={prevMonth}
              className="rounded-md px-2 py-1 text-sm text-neutral-600 hover:bg-neutral-100"
            >
              ←
            </button>
            <span className="text-sm font-medium text-neutral-900">
              {MONTHS[currentMonth]} {currentYear}
            </span>
            <button
              onClick={nextMonth}
              className="rounded-md px-2 py-1 text-sm text-neutral-600 hover:bg-neutral-100"
            >
              →
            </button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-7 gap-1">
          {DAYS.map((d) => (
            <div key={d} className="p-2 text-center text-xs font-medium text-neutral-500">
              {d}
            </div>
          ))}
          {Array.from({ length: firstDayOfWeek }).map((_, i) => (
            <div key={`empty-${i}`} />
          ))}
          {dates.map(({ day, hasEval, isToday }) => (
            <button
              key={day}
              type="button"
              onClick={() => handleDayClick(day)}
              className={`relative rounded-md p-2 text-center text-sm transition-colors ${
                isToday
                  ? 'bg-primary-100 font-bold text-primary-700'
                  : hasEval
                    ? 'bg-primary-50 font-medium text-primary-700 hover:bg-primary-100'
                    : 'text-neutral-700 hover:bg-neutral-100'
              } ${selectedDay === day ? 'ring-2 ring-primary-500' : ''}`}
            >
              {day}
              {hasEval && (
                <span className="absolute bottom-1 left-1/2 h-1 w-1 -translate-x-1/2 rounded-full bg-primary-500" />
              )}
            </button>
          ))}
        </div>

        {tooltipEvaluaciones && tooltipEvaluaciones.length > 0 && (
          <div className="mt-4 space-y-2 rounded-md border border-neutral-200 bg-neutral-50 p-4">
            <p className="text-sm font-medium text-neutral-700">
              Evaluaciones del {selectedDay}/{String(currentMonth + 1).padStart(2, '0')}/{currentYear}
            </p>
            {tooltipEvaluaciones.map((ev) => (
              <div key={ev.id} className="flex items-center gap-2 rounded-md bg-white p-2 text-sm shadow-sm">
                <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${TIPO_COLORS[ev.tipo] || 'bg-neutral-100 text-neutral-700'}`}>
                  {TIPO_LABELS[ev.tipo] || ev.tipo}
                </span>
                <span className="font-medium text-neutral-900">{ev.titulo}</span>
                <span className="text-neutral-500">— {ev.materia}</span>
                <span className="text-neutral-400">Inst. {ev.instancia}</span>
              </div>
            ))}
          </div>
        )}

        {(!evaluaciones || evaluaciones.length === 0) && (
          <div className="mt-4 rounded-lg border border-neutral-200 bg-neutral-50 p-4 text-center">
            <p className="text-sm text-neutral-600">No hay evaluaciones registradas</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function formatDateKey(year: number, month: number, day: number): string {
  return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}
