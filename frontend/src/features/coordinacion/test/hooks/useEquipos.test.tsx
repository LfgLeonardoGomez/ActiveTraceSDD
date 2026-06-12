import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useMisEquipos, useCrearAsignacion } from '../../hooks/useEquipos';
import * as api from '../../services/equipos.api';

vi.mock('../../services/equipos.api', () => ({
  getMisEquipos: vi.fn(),
  crearAsignacion: vi.fn(),
  getUsuarios: vi.fn(),
  getAsignaciones: vi.fn(),
  asignacionMasiva: vi.fn(),
  clonarEquipo: vi.fn(),
  actualizarVigencia: vi.fn(),
  crearUsuario: vi.fn(),
  actualizarUsuario: vi.fn(),
  getExportUrl: vi.fn(),
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('useMisEquipos', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns data on success', async () => {
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
    ];
    vi.mocked(api.getMisEquipos).mockResolvedValue(mockEquipos);

    const { result } = renderHook(() => useMisEquipos(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockEquipos);
  });

  it('shows error state on failure', async () => {
    vi.mocked(api.getMisEquipos).mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useMisEquipos(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.data).toBeUndefined();
  });
});

describe('useCrearAsignacion', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls the API and invalidates queries on success', async () => {
    const mockResponse = {
      id: 'a1',
      docente: 'Docente',
      docente_id: 'd1',
      materia: 'Matemática',
      materia_id: 'm1',
      carrera: 'Ingeniería',
      cohorte: '2024',
      cohorte_id: 'c1',
      rol: 'PROFESOR',
      fecha_desde: '2024-01-01',
      fecha_hasta: '2024-12-31',
      estado: 'activo',
    };
    vi.mocked(api.crearAsignacion).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useCrearAsignacion(), { wrapper: createWrapper() });

    const payload = {
      docente_id: 'd1',
      materia_id: 'm1',
      carrera_id: 'carr1',
      cohorte_id: 'c1',
      rol: 'PROFESOR',
      fecha_desde: '2024-01-01',
      fecha_hasta: '2024-12-31',
    };

    result.current.mutate(payload);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(api.crearAsignacion).toHaveBeenCalledWith(payload, expect.any(Object));
  });
});
