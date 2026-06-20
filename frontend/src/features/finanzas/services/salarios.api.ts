import api from '@/shared/services/api';
import { toList, type Paginated } from '@/shared/services/pagination';
import type {
  SalarioBase,
  SalarioBaseCreate,
  SalarioPlus,
  SalarioPlusCreate,
  SalarioFilters,
} from '../types/salarios.types';

// GET /api/v1/liquidaciones/salario-base
export async function getSalarioBase(filters?: SalarioFilters): Promise<SalarioBase[]> {
  const { data } = await api.get<SalarioBase[] | Paginated<SalarioBase>>('/api/v1/liquidaciones/salario-base', { params: filters });
  return toList(data);
}

// POST /api/v1/liquidaciones/salario-base
// Body: SalarioBaseCreate { rol, monto, desde, hasta? }
export async function crearSalarioBase(payload: SalarioBaseCreate): Promise<SalarioBase> {
  const { data } = await api.post<SalarioBase>('/api/v1/liquidaciones/salario-base', payload);
  return data;
}

// PATCH /api/v1/liquidaciones/salario-base/{id}
// Body: SalarioBaseUpdate { monto?, desde?, hasta? }
export async function actualizarSalarioBase(id: string, payload: Partial<SalarioBaseCreate>): Promise<SalarioBase> {
  const { data } = await api.patch<SalarioBase>(`/api/v1/liquidaciones/salario-base/${id}`, payload);
  return data;
}

// DELETE /api/v1/liquidaciones/salario-base/{id} — 204 No Content
export async function eliminarSalarioBase(id: string): Promise<void> {
  await api.delete(`/api/v1/liquidaciones/salario-base/${id}`);
}

// GET /api/v1/liquidaciones/salario-plus
export async function getSalarioPlus(filters?: SalarioFilters): Promise<SalarioPlus[]> {
  const { data } = await api.get<SalarioPlus[] | Paginated<SalarioPlus>>('/api/v1/liquidaciones/salario-plus', { params: filters });
  return toList(data);
}

// POST /api/v1/liquidaciones/salario-plus
// Body: SalarioPlusCreate { grupo, rol, descripcion?, monto, tope_acumulacion?, desde, hasta? }
export async function crearSalarioPlus(payload: SalarioPlusCreate): Promise<SalarioPlus> {
  const { data } = await api.post<SalarioPlus>('/api/v1/liquidaciones/salario-plus', payload);
  return data;
}

// PATCH /api/v1/liquidaciones/salario-plus/{id}
// Body: SalarioPlusUpdate { descripcion?, monto?, tope_acumulacion?, desde?, hasta? }
export async function actualizarSalarioPlus(id: string, payload: Partial<SalarioPlusCreate>): Promise<SalarioPlus> {
  const { data } = await api.patch<SalarioPlus>(`/api/v1/liquidaciones/salario-plus/${id}`, payload);
  return data;
}

// DELETE /api/v1/liquidaciones/salario-plus/{id} — 204 No Content
export async function eliminarSalarioPlus(id: string): Promise<void> {
  await api.delete(`/api/v1/liquidaciones/salario-plus/${id}`);
}
