import { useState, useEffect } from 'react';
import { useCohortesLiquidacion } from '../../hooks/useLiquidaciones';
import { Input } from '@/shared/components/ui/Input';
import { Button } from '@/shared/components/ui/Button';
import { Spinner } from '@/shared/components/ui/Spinner';

interface PeriodoSelectorProps {
  onChange: (cohorteId: string, mes: string) => void;
}

export default function PeriodoSelector({ onChange }: PeriodoSelectorProps) {
  const { data: cohortes, isLoading } = useCohortesLiquidacion();
  const [cohorteId, setCohorteId] = useState('');
  const [mes, setMes] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  });

  useEffect(() => {
    if (cohortes && cohortes.length > 0 && !cohorteId) {
      setCohorteId(cohortes[0].id);
    }
  }, [cohortes, cohorteId]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (cohorteId && mes) {
      onChange(cohorteId, mes);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 py-4">
        <Spinner size="sm" />
        <span className="text-sm text-muted-foreground">Cargando cohortes...</span>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3">
      <div className="space-y-2">
        <label htmlFor="cohorte" className="text-sm font-medium">
          Cohorte
        </label>
        <select
          id="cohorte"
          value={cohorteId}
          onChange={(e) => setCohorteId(e.target.value)}
          className="h-10 w-48 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
        >
          <option value="">Seleccionar...</option>
          {cohortes?.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nombre}
            </option>
          ))}
        </select>
      </div>

      <Input
        label="Mes"
        type="month"
        value={mes}
        onChange={(e) => setMes(e.target.value)}
        className="w-48"
      />

      <Button type="submit" disabled={!cohorteId || !mes}>
        Consultar
      </Button>
    </form>
  );
}
