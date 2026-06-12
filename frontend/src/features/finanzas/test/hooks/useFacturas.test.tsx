import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useFacturas } from '../../hooks/useFacturas';
import * as api from '../../services/facturas.api';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('useFacturas hook', () => {
  it('fetches facturas', async () => {
    const mockData = {
      items: [
        {
          id: '1',
          docente_id: 'd1',
          docente_nombre: 'Ana',
          periodo: '2024-06',
          monto: 30000,
          estado: 'pendiente' as const,
          fecha_subida: '2024-06-01T00:00:00Z',
        },
      ],
      total: 1,
    };
    vi.spyOn(api, 'getFacturas').mockResolvedValue(mockData);

    const { result } = renderHook(() => useFacturas(), { wrapper });

    await waitFor(() => expect(result.current.data).toEqual(mockData));
  });
});
