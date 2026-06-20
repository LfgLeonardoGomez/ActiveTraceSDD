import { useState } from 'react';
import { Input } from '@/shared/components/ui/Input';
import { Button } from '@/shared/components/ui/Button';

interface PeriodoSelectorProps {
  onChange: (cohorteId: string, periodo: string) => void;
}

export default function PeriodoSelector({ onChange }: PeriodoSelectorProps) {
  // NOTE: The /api/v1/liquidaciones/cohortes endpoint does not exist.
  // Cohorte selection is done via a free-text input until the correct endpoint is available.
  const [cohorteId, setCohorteId] = useState('');
  const [periodo, setPeriodo] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (cohorteId && periodo) {
      onChange(cohorteId, periodo);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3">
      <Input
        label="Cohorte ID"
        placeholder="UUID de la cohorte"
        value={cohorteId}
        onChange={(e) => setCohorteId(e.target.value)}
        className="w-64"
      />

      <Input
        label="Período"
        type="month"
        value={periodo}
        onChange={(e) => setPeriodo(e.target.value)}
        className="w-48"
      />

      <Button type="submit" disabled={!cohorteId || !periodo}>
        Consultar
      </Button>
    </form>
  );
}
