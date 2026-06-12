import { useState, useMemo } from 'react';
import { useOutletContext } from 'react-router-dom';
import { MonitorFilters } from './MonitorFilters';
import { MonitorTable } from './MonitorTable';
import { useMonitor } from '../hooks/useMonitor';
import { useDebounce } from '@/shared/hooks/useDebounce';
import { useAuth } from '@/shared/services/AuthContext';
import type { MonitorFilters as MonitorFiltersType } from '../types/comisiones.types';

export function MonitorTab() {
  const { materiaId } = useOutletContext<{ materiaId: string }>();
  const { user } = useAuth();
  const [filters, setFilters] = useState<MonitorFiltersType>({});
  const [page, setPage] = useState(1);
  const debouncedFilters = useDebounce(filters, 300);

  const esCoordinador = useMemo(
    () => user?.roles.some((r) => r.name === 'COORDINADOR') ?? false,
    [user],
  );

  const { data, isLoading, isError, refetch } = useMonitor(
    materiaId,
    debouncedFilters,
    page,
    esCoordinador,
  );

  const handleFiltersChange = (newFilters: MonitorFiltersType) => {
    setFilters(newFilters);
    setPage(1);
  };

  return (
    <div className="space-y-4">
      <MonitorFilters
        onFiltersChange={handleFiltersChange}
        isLoading={isLoading}
        showDateRange={esCoordinador}
      />
      <MonitorTable
        data={data?.data ?? []}
        total={data?.total ?? 0}
        page={data?.page ?? 1}
        totalPages={data?.total_pages ?? 1}
        isLoading={isLoading}
        isError={isError}
        onRefetch={refetch}
        onPageChange={setPage}
        esCoordinador={esCoordinador}
      />
    </div>
  );
}
