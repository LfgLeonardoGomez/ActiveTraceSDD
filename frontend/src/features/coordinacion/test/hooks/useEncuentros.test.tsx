import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEncuentros, useCrearRecurrente } from '../../hooks/useEncuentros';
import * as api from '../../services/encuentros.api';

vi.mock('../../services/encuentros.api', () => ({
  getEncuentros: vi.fn(),
  crearRecurrente: vi.fn(),
  crearEncuentro: vi.fn(),
  editarEncuentro: vi.fn(),
  getContenidoAula: vi.fn(),
  getGuardias: vi.fn(),
  registrarGuardia: vi.fn(),
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

describe('useEncuentros', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns list of encuentros on success', async () => {
    const mockEncuentros = [
      {
        id: 'e1',
        materia: 'Matemática',
        materia_id: 'm1',
        cohorte: '2024',
        cohorte_id: 'c1',
        docente: 'Juan Pérez',
        docente_id: 'd1',
        fecha: '2024-06-15',
        hora: '10:00',
        titulo: 'Clase 1',
        estado: 'programado' as const,
        enlace: 'https://zoom.us/j/123',
        grabacion: null,
        comentario_interno: null,
      },
    ];
    vi.mocked(api.getEncuentros).mockResolvedValue(mockEncuentros);

    const { result } = renderHook(() => useEncuentros({ materia_id: 'm1' }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockEncuentros);
    expect(api.getEncuentros).toHaveBeenCalledWith({ materia_id: 'm1' });
  });
});

describe('useCrearRecurrente', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls crearRecurrente and invalidates on success', async () => {
    const mockResponse = {
      instancias: [
        {
          id: 'e1',
          materia: 'Matemática',
          materia_id: 'm1',
          cohorte: '2024',
          cohorte_id: 'c1',
          docente: 'Juan Pérez',
          docente_id: 'd1',
          fecha: '2024-06-15',
          hora: '10:00',
          titulo: 'Clase 1',
          estado: 'programado' as const,
          enlace: null,
          grabacion: null,
          comentario_interno: null,
        },
      ],
      count: 1,
    };
    vi.mocked(api.crearRecurrente).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useCrearRecurrente(), { wrapper: createWrapper() });

    const payload = {
      materia_id: 'm1',
      dia_semana: 1 as const,
      horario: '10:00',
      fecha_inicio: '2024-06-15',
      semanas: 4,
      titulo: 'Clase semanal',
    };

    result.current.mutate(payload);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(api.crearRecurrente).toHaveBeenCalledWith(payload, expect.any(Object));
  });
});
