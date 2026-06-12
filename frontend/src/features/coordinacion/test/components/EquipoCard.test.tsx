import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EquipoCard } from '../../components/equipos/EquipoCard';

vi.mock('../../hooks/useEquipos', () => ({
  useMisEquipos: vi.fn(),
}));

import { useMisEquipos } from '../../hooks/useEquipos';

describe('EquipoCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading skeleton', () => {
    vi.mocked(useMisEquipos).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    } as never);

    const { container } = render(<EquipoCard />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons).toHaveLength(3);
  });

  it('renders empty state', () => {
    vi.mocked(useMisEquipos).mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as never);

    render(<EquipoCard />);
    expect(screen.getByText('No tenés equipos asignados')).toBeInTheDocument();
  });

  it('renders equipo data correctly', () => {
    const mockEquipos = [
      {
        id: '1',
        materia: 'Matemática',
        materia_id: 'm1',
        carrera: 'Ingeniería',
        cohorte: '2024',
        cohorte_id: 'c1',
        roles: ['PROFESOR'],
        vigencia_desde: '2024-01-01',
        vigencia_hasta: '2024-12-31',
        estado: 'activo',
      },
      {
        id: '2',
        materia: 'Física',
        materia_id: 'm2',
        carrera: 'Ingeniería',
        cohorte: '2024',
        cohorte_id: 'c1',
        roles: ['TUTOR'],
        vigencia_desde: '2024-03-01',
        vigencia_hasta: '2024-12-31',
        estado: 'activo',
      },
    ];

    vi.mocked(useMisEquipos).mockReturnValue({
      data: mockEquipos,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as never);

    render(<EquipoCard />);
    expect(screen.getByText('Mostrando 2 asignaciones')).toBeInTheDocument();
    expect(screen.getByText('Matemática')).toBeInTheDocument();
    expect(screen.getByText('Física')).toBeInTheDocument();
    expect(screen.getAllByText('Ingeniería').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('2024').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('PROFESOR')).toBeInTheDocument();
    expect(screen.getByText('TUTOR')).toBeInTheDocument();
  });

  it('renders error state with Reintentar', () => {
    const mockRefetch = vi.fn();
    vi.mocked(useMisEquipos).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      refetch: mockRefetch,
    } as never);

    render(<EquipoCard />);
    expect(screen.getByText('Error al cargar tus equipos')).toBeInTheDocument();
    expect(screen.getByText('Reintentar')).toBeInTheDocument();
  });
});
