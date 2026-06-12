import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/shared/components/ui/Button';
import { Spinner } from '@/shared/components/ui/Spinner';
import { useAuditLog, useCatalogoAcciones } from '../hooks/useAuditoria';
import LogFilters from '../components/auditoria/LogFilters';
import LogTable from '../components/auditoria/LogTable';
import type { AuditLogFilters } from '../types/auditoria.types';

export default function AuditoriaLogPage() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<AuditLogFilters>({ page: 1, page_size: 50 });
  const { data, isLoading } = useAuditLog(filters);
  const { data: catalogo, isLoading: catalogoLoading } = useCatalogoAcciones();

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Log de auditoría</h1>
        <Button variant="outline" onClick={() => navigate('/admin/auditoria')}>
          Volver al panel
        </Button>
      </div>

      <LogFilters
        filters={filters}
        onChange={setFilters}
        catalogoAcciones={catalogo ?? []}
      />

      {isLoading && (
        <div className="flex items-center gap-2 py-8">
          <Spinner />
          <span className="text-muted-foreground">Cargando log...</span>
        </div>
      )}

      {data && (
        <LogTable
          items={data.items}
          total={data.total}
          page={filters.page ?? 1}
          pageSize={filters.page_size ?? 50}
          onPageChange={handlePageChange}
        />
      )}
    </div>
  );
}
