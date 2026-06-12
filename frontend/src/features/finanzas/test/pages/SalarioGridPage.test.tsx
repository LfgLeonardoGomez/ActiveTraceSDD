import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import SalarioGridPage from '../../pages/SalarioGridPage';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

vi.mock('../../services/salarios.api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../services/salarios.api')>();
  return {
    ...actual,
    getSalarioBase: vi.fn().mockResolvedValue([]),
    getSalarioPlus: vi.fn().mockResolvedValue([]),
  };
});

describe('SalarioGridPage', () => {
  it('renders tabs', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <SalarioGridPage />
        </BrowserRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByText('Grilla salarial')).toBeInTheDocument();
    expect(await screen.findByText('Salario base')).toBeInTheDocument();
    expect(await screen.findByText('Salario plus')).toBeInTheDocument();
  });
});
