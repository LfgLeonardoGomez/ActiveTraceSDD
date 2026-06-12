import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MetricasPanel } from '../../components/coloquios/MetricasPanel';

vi.mock('../../hooks/useColoquios', () => ({
  useMetricasColoquios: vi.fn(),
}));

import { useMetricasColoquios } from '../../hooks/useColoquios';

describe('MetricasPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders 4 skeleton cards on loading', () => {
    vi.mocked(useMetricasColoquios).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    } as never);

    const { container } = render(<MetricasPanel />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons).toHaveLength(4);
  });

  it('renders zero state with grey icons', () => {
    vi.mocked(useMetricasColoquios).mockReturnValue({
      data: {
        total_alumnos_cargados: 0,
        instancias_activas: 0,
        reservas_activas: 0,
        notas_registradas: 0,
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as never);

    render(<MetricasPanel />);

    expect(screen.getByText('Métricas de coloquios')).toBeInTheDocument();
    expect(screen.getByText('Total alumnos cargados')).toBeInTheDocument();
    expect(screen.getByText('Instancias activas')).toBeInTheDocument();
    expect(screen.getByText('Reservas activas')).toBeInTheDocument();
    expect(screen.getByText('Notas registradas')).toBeInTheDocument();
    expect(screen.getByText('Actualizar')).toBeInTheDocument();

    const zeroValues = screen.getAllByText('0');
    expect(zeroValues).toHaveLength(4);
  });

  it('renders data correctly', () => {
    vi.mocked(useMetricasColoquios).mockReturnValue({
      data: {
        total_alumnos_cargados: 150,
        instancias_activas: 8,
        reservas_activas: 42,
        notas_registradas: 310,
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as never);

    render(<MetricasPanel />);

    expect(screen.getByText('150')).toBeInTheDocument();
    expect(screen.getByText('8')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('310')).toBeInTheDocument();
  });

  it('renders error state with Reintentar', () => {
    const mockRefetch = vi.fn();
    vi.mocked(useMetricasColoquios).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      refetch: mockRefetch,
    } as never);

    render(<MetricasPanel />);
    expect(screen.getByText('Error al cargar métricas')).toBeInTheDocument();
    expect(screen.getByText('Reintentar')).toBeInTheDocument();
  });
});
