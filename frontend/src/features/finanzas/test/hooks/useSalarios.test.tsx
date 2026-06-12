import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useSalarioBase, useSalarioPlus } from '../../hooks/useSalarios';
import * as api from '../../services/salarios.api';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('useSalarios hooks', () => {
  it('fetches salario base', async () => {
    const mockData = [
      { id: '1', rol: 'TUTOR', monto: 50000, vigencia_desde: '2024-01-01', vigencia_hasta: '2024-12-31' },
    ];
    vi.spyOn(api, 'getSalarioBase').mockResolvedValue(mockData);

    const { result } = renderHook(() => useSalarioBase(), { wrapper });

    await waitFor(() => expect(result.current.data).toEqual(mockData));
  });

  it('fetches salario plus', async () => {
    const mockData = [
      { id: '2', grupo: 'A', rol: 'TUTOR', monto: 10000, vigencia_desde: '2024-01-01', vigencia_hasta: '2024-12-31' },
    ];
    vi.spyOn(api, 'getSalarioPlus').mockResolvedValue(mockData);

    const { result } = renderHook(() => useSalarioPlus(), { wrapper });

    await waitFor(() => expect(result.current.data).toEqual(mockData));
  });
});
