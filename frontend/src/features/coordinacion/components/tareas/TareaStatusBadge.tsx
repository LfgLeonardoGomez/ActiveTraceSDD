import { useState, useRef, useEffect } from 'react';
import type { TareaEstado } from '../../types/tareas.types';

const COLOR_MAP: Record<TareaEstado, string> = {
  pendiente: 'bg-neutral-100 text-neutral-700',
  en_proceso: 'bg-blue-100 text-blue-700',
  completada: 'bg-green-100 text-green-700',
  aprobada: 'bg-emerald-100 text-emerald-700',
  rechazada: 'bg-red-100 text-red-700',
};

const LABEL_MAP: Record<TareaEstado, string> = {
  pendiente: 'Pendiente',
  en_proceso: 'En proceso',
  completada: 'Completada',
  aprobada: 'Aprobada',
  rechazada: 'Rechazada',
};

const TRANSITIONS: Partial<Record<TareaEstado, TareaEstado[]>> = {
  pendiente: ['en_proceso'],
  en_proceso: ['completada'],
};

interface TareaStatusBadgeProps {
  estado: TareaEstado;
  canChange?: boolean;
  onEstadoChange?: (nuevoEstado: TareaEstado) => void;
}

export function TareaStatusBadge({ estado, canChange = false, onEstadoChange }: TareaStatusBadgeProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const transitions = TRANSITIONS[estado];

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleChange = (next: TareaEstado) => {
    onEstadoChange?.(next);
    setOpen(false);
  };

  return (
    <div ref={ref} className="relative inline-block">
      <button
        type="button"
        onClick={() => canChange && transitions?.length ? setOpen(!open) : undefined}
        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${COLOR_MAP[estado]} ${
          canChange && transitions?.length ? 'cursor-pointer hover:ring-2 hover:ring-primary-400' : 'cursor-default'
        }`}
      >
        {LABEL_MAP[estado]}
      </button>

      {open && canChange && transitions && (
        <div className="absolute left-0 top-full z-10 mt-1 w-36 rounded-md border border-neutral-200 bg-white shadow-lg">
          {transitions.map((next) => (
            <button
              key={next}
              type="button"
              onClick={() => handleChange(next)}
              className={`flex w-full items-center px-3 py-2 text-left text-xs font-medium transition-colors hover:bg-neutral-50 ${COLOR_MAP[next]}`}
            >
              {LABEL_MAP[next]}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export function getStatusLabel(estado: TareaEstado): string {
  return LABEL_MAP[estado];
}

export function getStatusColor(estado: TareaEstado): string {
  return COLOR_MAP[estado];
}
