import api from '@/shared/services/api';
import type {
  SalarioBase,
  SalarioBaseCreate,
  SalarioPlus,
  SalarioPlusCreate,
  SalarioFilters,
} from '../types/salarios.types';

export async function getSalarioBase(filters?: SalarioFilters): Promise<SalarioBase[]> {
  const { data } = await api.get<SalarioBase[]>('/api/liquidaciones/salario-base', { params: filters });
  return data;
}

export async function crearSalarioBase(payload: SalarioBaseCreate): Promise<SalarioBase> {
  const { data } = await api.post<SalarioBase>('/api/liquidaciones/salario-base', payload);
  return data;
}

export async function actualizarSalarioBase(id: string, payload: Partial<SalarioBaseCreate>): Promise<SalarioBase> {
  const { data } = await api.patch<SalarioBase>(`/api/liquidaciones/salario-base/${id}`, payload);
  return data;
}

export async function eliminarSalarioBase(id: string): Promise<void> {
  await api.delete(`/api/liquidaciones/salario-base/${id}`);
}

export async function getSalarioPlus(filters?: SalarioFilters): Promise<SalarioPlus[]> {
  const { data } = await api.get<SalarioPlus[]>('/api/liquidaciones/salario-plus', { params: filters });
  return data;
}

export async function crearSalarioPlus(payload: SalarioPlusCreate): Promise<SalarioPlus> {
  const { data } = await api.post<SalarioPlus>('/api/liquidaciones/salario-plus', payload);
  return data;
}

export async function actualizarSalarioPlus(id: string, payload: Partial<SalarioPlusCreate>): Promise<SalarioPlus> {
  const { data } = await api.patch<SalarioPlus>(`/api/liquidaciones/salario-plus/${id}`, payload);
  return data;
}

export async function eliminarSalarioPlus(id: string): Promise<void> {
  await api.delete(`/api/liquidaciones/salario-plus/${id}`);
}
