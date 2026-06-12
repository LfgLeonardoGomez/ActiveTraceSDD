import { useEffect, useState } from 'react';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardContent } from '@/shared/components/ui/Card';
import type { AuditLogFilters } from '../../types/auditoria.types';

interface LogFiltersProps {
  filters: AuditLogFilters;
  onChange: (filters: AuditLogFilters) => void;
  catalogoAcciones: { codigo: string; descripcion: string }[];
}

export default function LogFilters({ filters, onChange, catalogoAcciones }: LogFiltersProps) {
  const [local, setLocal] = useState(filters);

  useEffect(() => {
    setLocal(filters);
  }, [filters]);

  const handleChange = (key: keyof AuditLogFilters, value: unknown) => {
    setLocal((prev) => ({ ...prev, [key]: value, page: 1 }));
  };

  const handleApply = () => {
    onChange(local);
  };

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex flex-wrap items-end gap-3">
          <Input
            label="Desde"
            type="date"
            value={local.fecha_desde ?? ''}
            onChange={(e) => handleChange('fecha_desde', e.target.value || undefined)}
            className="w-44"
          />
          <Input
            label="Hasta"
            type="date"
            value={local.fecha_hasta ?? ''}
            onChange={(e) => handleChange('fecha_hasta', e.target.value || undefined)}
            className="w-44"
          />
          <div className="space-y-2">
            <label className="text-sm font-medium">Acción</label>
            <select
              value={local.accion ?? ''}
              onChange={(e) => handleChange('accion', e.target.value || undefined)}
              className="h-10 w-48 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
            >
              <option value="">Todas</option>
              {catalogoAcciones.map((a) => (
                <option key={a.codigo} value={a.codigo}>
                  {a.descripcion}
                </option>
              ))}
            </select>
          </div>
          <Input
            label="Usuario ID"
            placeholder="UUID..."
            value={local.usuario_id ?? ''}
            onChange={(e) => handleChange('usuario_id', e.target.value || undefined)}
            className="w-56"
          />
          <Input
            label="Materia ID"
            placeholder="UUID..."
            value={local.materia_id ?? ''}
            onChange={(e) => handleChange('materia_id', e.target.value || undefined)}
            className="w-56"
          />
          <Input
            label="Estado"
            placeholder="Estado..."
            value={local.estado ?? ''}
            onChange={(e) => handleChange('estado', e.target.value || undefined)}
            className="w-32"
          />
          <Button onClick={handleApply}>Aplicar</Button>
        </div>
      </CardContent>
    </Card>
  );
}


