import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AsignacionForm } from '../../components/equipos/AsignacionForm';

vi.mock('../../hooks/useEquipos', () => ({
  useCrearAsignacion: vi.fn(),
  useMisEquipos: vi.fn(),
  useUsuarios: vi.fn(),
  useAsignaciones: vi.fn(),
}));

import { useCrearAsignacion } from '../../hooks/useEquipos';

describe('AsignacionForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders form with all fields', () => {
    vi.mocked(useCrearAsignacion).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
      data: undefined,
      error: null,
      isError: false,
      isIdle: true,
      isPaused: false,
      isSuccess: false,
      failureCount: 0,
      failureReason: null,
      status: 'idle',
      submittedAt: 0,
      variables: undefined,
      reset: vi.fn(),
      mutate: vi.fn(),
      context: undefined,
    });

    render(<AsignacionForm />);

    expect(screen.getByText('Nueva Asignación')).toBeInTheDocument();
    expect(screen.getByLabelText('Docente ID')).toBeInTheDocument();
    expect(screen.getByLabelText('Materia ID')).toBeInTheDocument();
    expect(screen.getByLabelText('Carrera ID')).toBeInTheDocument();
    expect(screen.getByLabelText('Cohorte ID')).toBeInTheDocument();
    expect(screen.getByLabelText('Rol')).toBeInTheDocument();
    expect(screen.getByLabelText('Fecha desde')).toBeInTheDocument();
    expect(screen.getByLabelText('Fecha hasta')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /crear asignación/i })).toBeInTheDocument();
  });

  it('shows validation error when submitted empty', async () => {
    vi.mocked(useCrearAsignacion).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
      data: undefined,
      error: null,
      isError: false,
      isIdle: true,
      isPaused: false,
      isSuccess: false,
      failureCount: 0,
      failureReason: null,
      status: 'idle',
      submittedAt: 0,
      variables: undefined,
      reset: vi.fn(),
      mutate: vi.fn(),
      context: undefined,
    });

    render(<AsignacionForm />);

    const submitButton = screen.getByRole('button', { name: /crear asignación/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Docente requerido')).toBeInTheDocument();
    });
    expect(screen.getByText('Materia requerida')).toBeInTheDocument();
    expect(screen.getByText('Carrera requerida')).toBeInTheDocument();
    expect(screen.getByText('Cohorte requerida')).toBeInTheDocument();
    expect(screen.getByText('Rol requerido')).toBeInTheDocument();
    expect(screen.getByText('Fecha desde requerida')).toBeInTheDocument();
    expect(screen.getByText('Fecha hasta requerida')).toBeInTheDocument();
  });

  it('calls mutation on valid submit', async () => {
    const mockMutateAsync = vi.fn().mockResolvedValue({});
    vi.mocked(useCrearAsignacion).mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
      data: undefined,
      error: null,
      isError: false,
      isIdle: true,
      isPaused: false,
      isSuccess: false,
      failureCount: 0,
      failureReason: null,
      status: 'idle',
      submittedAt: 0,
      variables: undefined,
      reset: vi.fn(),
      mutate: vi.fn(),
      context: undefined,
    });

    render(<AsignacionForm />);

    fireEvent.change(screen.getByLabelText('Docente ID'), { target: { value: 'd1' } });
    fireEvent.change(screen.getByLabelText('Materia ID'), { target: { value: 'm1' } });
    fireEvent.change(screen.getByLabelText('Carrera ID'), { target: { value: 'carr1' } });
    fireEvent.change(screen.getByLabelText('Cohorte ID'), { target: { value: 'c1' } });
    fireEvent.change(screen.getByLabelText('Rol'), { target: { value: 'PROFESOR' } });
    fireEvent.change(screen.getByLabelText('Fecha desde'), { target: { value: '2024-01-01' } });
    fireEvent.change(screen.getByLabelText('Fecha hasta'), { target: { value: '2024-12-31' } });

    const submitButton = screen.getByRole('button', { name: /crear asignación/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        docente_id: 'd1',
        materia_id: 'm1',
        carrera_id: 'carr1',
        cohorte_id: 'c1',
        rol: 'PROFESOR',
        fecha_desde: '2024-01-01',
        fecha_hasta: '2024-12-31',
      });
    });
  });
});
