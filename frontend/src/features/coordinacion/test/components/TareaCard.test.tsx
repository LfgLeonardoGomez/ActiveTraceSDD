import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TareaCard } from '../../components/tareas/TareaCard';

vi.mock('../../hooks/useTareas', () => ({
  useMisTareas: vi.fn(),
  useActualizarEstadoTarea: () => ({
    mutate: vi.fn(),
    isPending: false,
    isSuccess: false,
    isError: false,
    error: null,
    data: undefined,
    reset: vi.fn(),
    status: 'idle',
  }),
}));

vi.mock('../../components/tareas/TareaStatusBadge', () => ({
  TareaStatusBadge: ({ estado }: { estado: string }) => (
    <span data-testid="status-badge">{estado}</span>
  ),
}));

vi.mock('../../components/tareas/TareaCommentThread', () => ({
  TareaCommentThread: () => <div data-testid="comment-thread" />,
}));

import { useMisTareas } from '../../hooks/useTareas';

describe('TareaCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders 3 skeleton cards on loading', () => {
    vi.mocked(useMisTareas).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    } as never);

    const { container } = render(<TareaCard />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons).toHaveLength(3);
  });

  it('renders empty state', () => {
    vi.mocked(useMisTareas).mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as never);

    render(<TareaCard />);
    expect(screen.getByText('No tenés tareas asignadas')).toBeInTheDocument();
    expect(
      screen.getByText('Cuando te asignen una tarea, aparecerá acá'),
    ).toBeInTheDocument();
  });

  it('renders card data correctly', () => {
    vi.mocked(useMisTareas).mockReturnValue({
      data: [
        {
          id: 't1',
          titulo: 'Corregir TP1',
          descripcion: 'Corregir los trabajos prácticos',
          asignado: 'Yo',
          asignado_id: 'u1',
          asignador: 'Coordinador',
          asignador_id: 'u2',
          materia: 'Matemática',
          estado: 'pendiente' as const,
          prioridad: 'alta',
          fecha_creacion: '2024-06-01T00:00:00Z',
          fecha_limite: '2024-06-15T00:00:00Z',
          comentarios: [],
        },
      ],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as never);

    render(<TareaCard />);

    expect(screen.getByText('Corregir TP1')).toBeInTheDocument();
    expect(screen.getByText('Coordinador')).toBeInTheDocument();
    expect(screen.getByText('Matemática')).toBeInTheDocument();
    expect(screen.getByText('pendiente')).toBeInTheDocument();
    expect(screen.getByText('Tomar en proceso')).toBeInTheDocument();
  });
});
