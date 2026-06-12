import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AvisoCard } from '../../components/avisos/AvisoCard';

vi.mock('../../hooks/useAvisos', () => ({
  useAvisos: vi.fn(),
  useCrearAviso: vi.fn(),
  useEditarAviso: vi.fn(),
  useEliminarAviso: vi.fn(),
  useConfirmarAck: vi.fn(),
}));

import { useAvisos } from '../../hooks/useAvisos';

describe('AvisoCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders 3 skeleton cards on loading', () => {
    vi.mocked(useAvisos).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    } as never);

    const { container } = render(<AvisoCard />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons).toHaveLength(3);
  });

  it('renders empty state', () => {
    vi.mocked(useAvisos).mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as never);

    render(<AvisoCard />);
    expect(screen.getByText('No hay avisos publicados')).toBeInTheDocument();
  });

  it('renders card with severity badge', () => {
    vi.mocked(useAvisos).mockReturnValue({
      data: [
        {
          id: 'a1',
          titulo: 'Aviso importante',
          cuerpo: 'Este es un aviso crítico para todos',
          alcance: 'global' as const,
          materia_id: null,
          cohorte_id: null,
          roles_destinatarios: ['PROFESOR', 'TUTOR'],
          severidad: 'critico' as const,
          estado: 'publicado',
          fecha_desde: '2024-06-01T00:00:00Z',
          fecha_hasta: '2024-06-30T00:00:00Z',
          requiere_ack: true,
          creado: '2024-06-01T00:00:00Z',
          total_destinatarios: 10,
          leidos: 3,
        },
      ],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as never);

    render(<AvisoCard />);

    expect(screen.getByText('Aviso importante')).toBeInTheDocument();
    expect(screen.getByText('critico')).toBeInTheDocument();
    expect(screen.getByText('publicado')).toBeInTheDocument();
    expect(screen.getAllByText('Global').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/3\/10/)).toBeInTheDocument();
    expect(screen.getByText('Requiere ack: Sí')).toBeInTheDocument();
  });
});
