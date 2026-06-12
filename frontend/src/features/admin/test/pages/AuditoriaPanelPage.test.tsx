import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import AuditoriaPanelPage from '../../pages/AuditoriaPanelPage';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

vi.mock('../../services/auditoria.api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../services/auditoria.api')>();
  return {
    ...actual,
    getAccionesPorDia: vi.fn().mockResolvedValue([]),
    getComunicacionesPorDocente: vi.fn().mockResolvedValue([]),
    getInteraccionesPorDocenteMateria: vi.fn().mockResolvedValue([]),
    getUltimasAcciones: vi.fn().mockResolvedValue([]),
  };
});

describe('AuditoriaPanelPage', () => {
  it('renders panel title', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AuditoriaPanelPage />
        </BrowserRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByText('Auditoría')).toBeInTheDocument();
    expect(await screen.findByText('Ver log completo')).toBeInTheDocument();
  });
});
