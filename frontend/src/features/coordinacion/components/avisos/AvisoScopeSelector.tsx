import { useId } from 'react';

type Scope = 'global' | 'materia' | 'cohorte';

const ROLES = ['TUTOR', 'PROFESOR', 'COORDINADOR', 'ADMIN', 'FINANZAS', 'NEXO'] as const;

interface AvisoScopeSelectorProps {
  alcance: Scope;
  onAlcanceChange: (scope: Scope) => void;
  materia_id: string;
  onMateriaChange: (val: string) => void;
  cohorte_id: string;
  onCohorteChange: (val: string) => void;
  roles: string[];
  onRolesChange: (roles: string[]) => void;
  materias: { id: string; nombre: string }[];
  cohortes: { id: string; nombre: string }[];
}

export function AvisoScopeSelector({
  alcance,
  onAlcanceChange,
  materia_id,
  onMateriaChange,
  cohorte_id,
  onCohorteChange,
  roles,
  onRolesChange,
  materias,
  cohortes,
}: AvisoScopeSelectorProps) {
  const uid = useId();

  const toggleRole = (role: string) => {
    if (roles.includes(role)) {
      onRolesChange(roles.filter((r) => r !== role));
    } else {
      onRolesChange([...roles, role]);
    }
  };

  return (
    <div className="space-y-6">
      <fieldset>
        <legend className="text-sm font-medium text-neutral-900 mb-2">Alcance</legend>
        <div className="flex gap-4">
          {(['global', 'materia', 'cohorte'] as Scope[]).map((opt) => (
            <label key={opt} className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name={`${uid}-alcance`}
                value={opt}
                checked={alcance === opt}
                onChange={() => onAlcanceChange(opt)}
                className="text-primary-600"
              />
              <span className="text-sm capitalize text-neutral-700">{opt}</span>
            </label>
          ))}
        </div>
      </fieldset>

      {alcance === 'materia' && (
        <div>
          <label htmlFor={`${uid}-materia`} className="text-sm font-medium text-neutral-900">
            Materia
          </label>
          <select
            id={`${uid}-materia`}
            value={materia_id}
            onChange={(e) => onMateriaChange(e.target.value)}
            className="mt-1 flex h-10 w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm"
          >
            <option value="">Seleccionar materia</option>
            {materias.map((m) => (
              <option key={m.id} value={m.id}>{m.nombre}</option>
            ))}
          </select>
        </div>
      )}

      {alcance === 'cohorte' && (
        <div>
          <label htmlFor={`${uid}-cohorte`} className="text-sm font-medium text-neutral-900">
            Cohorte
          </label>
          <select
            id={`${uid}-cohorte`}
            value={cohorte_id}
            onChange={(e) => onCohorteChange(e.target.value)}
            className="mt-1 flex h-10 w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm"
          >
            <option value="">Seleccionar cohorte</option>
            {cohortes.map((c) => (
              <option key={c.id} value={c.id}>{c.nombre}</option>
            ))}
          </select>
        </div>
      )}

      <fieldset>
        <legend className="text-sm font-medium text-neutral-900 mb-2">
          Visible para roles
        </legend>
        <div className="flex flex-wrap gap-4">
          {ROLES.map((role) => (
            <label key={role} className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={roles.includes(role)}
                onChange={() => toggleRole(role)}
                className="text-primary-600 rounded"
              />
              <span className="text-sm text-neutral-700">{role}</span>
            </label>
          ))}
        </div>
      </fieldset>
    </div>
  );
}
