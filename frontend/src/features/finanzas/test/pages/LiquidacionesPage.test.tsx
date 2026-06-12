import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import LiquidacionesPage from '../../pages/LiquidacionesPage';
import * as api from '../../services/liquidaciones.api';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

vi.mock('../../services/liquidaciones.api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../services/liquidaciones.api')>();
  return {
    ...actual,
    getCohortes: vi.fn().mockResolvedValue([{ id: 'c1', nombre: 'Cohorte 2024' }]),
    getLiquidacion: vi.fn().mockResolvedValue({
      periodo: '2024-06',
      estado: 'abierto',
      segmento_general: [],
      segmento_nexo: [],
      segmento_facturantes: [],
      total_sin_factura: 0,
      total_con_factura: 0,
    }),
  };
});

describe('LiquidacionesPage', () => {
  it('renders period selector', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <LiquidacionesPage />
        </BrowserRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByText('Liquidaciones')).toBeInTheDocument();
    expect(await screen.findByText('Cohorte')).toBeInTheDocument();
  });
});
