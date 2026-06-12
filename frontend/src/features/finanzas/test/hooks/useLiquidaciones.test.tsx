import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useLiquidacion, useHistorial } from '../../hooks/useLiquidaciones';
import * as api from '../../services/liquidaciones.api';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('useLiquidaciones hooks', () => {
  it('fetches liquidacion', async () => {
    const mockData = {
      periodo: '2024-06',
      estado: 'abierto' as const,
      segmento_general: [],
      segmento_nexo: [],
      segmento_facturantes: [],
      total_sin_factura: 0,
      total_con_factura: 0,
    };
    vi.spyOn(api, 'getLiquidacion').mockResolvedValue(mockData);

    const { result } = renderHook(() => useLiquidacion('cohorte-1', '2024-06'), { wrapper });

    await waitFor(() => expect(result.current.data).toEqual(mockData));
  });

  it('fetches historial', async () => {
    const mockData = { items: [], total: 0 };
    vi.spyOn(api, 'getHistorial').mockResolvedValue(mockData);

    const { result } = renderHook(() => useHistorial(), { wrapper });

    await waitFor(() => expect(result.current.data).toEqual(mockData));
  });
});
