import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAccionesPorDia, useAuditLog } from '../../hooks/useAuditoria';
import * as api from '../../services/auditoria.api';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('useAuditoria hooks', () => {
  it('fetches acciones por dia', async () => {
    const mockData = [{ fecha: '2024-06-01', cantidad: 5 }];
    vi.spyOn(api, 'getAccionesPorDia').mockResolvedValue(mockData);

    const { result } = renderHook(() => useAccionesPorDia(), { wrapper });

    await waitFor(() => expect(result.current.data).toEqual(mockData));
  });

  it('fetches audit log', async () => {
    const mockData = { items: [], total: 0 };
    vi.spyOn(api, 'getAuditLog').mockResolvedValue(mockData);

    const { result } = renderHook(() => useAuditLog(), { wrapper });

    await waitFor(() => expect(result.current.data).toEqual(mockData));
  });
});
