import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EncuentroTable } from '../../components/encuentros/EncuentroTable';

vi.mock('../../hooks/useEncuentros', () => ({
  useEncuentros: vi.fn(),
}));

import { useEncuentros } from '../../hooks/useEncuentros';

const mockEncuentro = {
  id: 'e1',
  materia: 'Matemática',
  materia_id: 'm1',
  cohorte: '2024',
  cohorte_id: 'c1',
  docente: 'Juan Pérez',
  docente_id: 'd1',
  fecha: '2024-06-15T10:00:00Z',
  hora: '10:00',
  titulo: 'Clase 1',
  estado: 'programado' as const,
  enlace: 'https://zoom.us/j/123',
  grabacion: null,
  comentario_interno: null,
};

describe('EncuentroTable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading skeleton', () => {
    vi.mocked(useEncuentros).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    } as never);

    const { container } = render(<EncuentroTable />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons).toHaveLength(5);
  });

  it('renders empty state', () => {
    vi.mocked(useEncuentros).mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as never);

    render(<EncuentroTable />);
    expect(screen.getByText('No hay encuentros programados')).toBeInTheDocument();
  });

  it('renders table with data rows', () => {
    vi.mocked(useEncuentros).mockReturnValue({
      data: [mockEncuentro],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as never);

    render(<EncuentroTable />);

    expect(screen.getByText('Encuentros')).toBeInTheDocument();
    expect(screen.getByText('Matemática')).toBeInTheDocument();
    expect(screen.getByText('2024')).toBeInTheDocument();
    expect(screen.getByText('Juan Pérez')).toBeInTheDocument();
    expect(screen.getByText('10:00')).toBeInTheDocument();
    expect(screen.getByText('Clase 1')).toBeInTheDocument();
    expect(screen.getAllByText('Programado').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Abrir')).toBeInTheDocument();
    expect(screen.getByText('Editar')).toBeInTheDocument();

    expect(screen.queryByText('No hay encuentros programados')).not.toBeInTheDocument();
  });
});
