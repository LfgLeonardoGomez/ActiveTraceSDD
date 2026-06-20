import { useId } from 'react';
import { useNavigate } from 'react-router-dom';
import { useComisiones } from '../hooks/useComisiones';

interface ComisionSwitcherProps {
  /** The active comisión id (= asignacion_id), from the route param. */
  currentId: string;
}

/**
 * Compact comisión selector shown inside the comisión detail layout so the user
 * can switch comisiones without going back to the index. Navigates by id
 * (= asignacion_id), which the analytics endpoints key off.
 */
export function ComisionSwitcher({ currentId }: ComisionSwitcherProps) {
  const selectId = useId();
  const navigate = useNavigate();
  const { data: comisiones } = useComisiones();

  if (!comisiones || comisiones.length === 0) {
    return null;
  }

  return (
    <div className="flex items-center gap-3">
      <label htmlFor={selectId} className="text-sm font-medium text-neutral-700">
        Comisión
      </label>
      <select
        id={selectId}
        value={currentId}
        onChange={(e) => {
          if (e.target.value) navigate(`/comisiones/${e.target.value}`);
        }}
        className="rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
      >
        {comisiones.map((c) => (
          <option key={c.id} value={c.id}>
            {c.materia_nombre} — {c.cohorte_nombre}
          </option>
        ))}
      </select>
    </div>
  );
}
