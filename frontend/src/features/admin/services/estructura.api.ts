import api from '@/shared/services/api';
import { toList, type Paginated } from '@/shared/services/pagination';
import type {
  Carrera,
  CarreraCreate,
  Cohorte,
  CohorteCreate,
  Materia,
  MateriaCreate,
  EstructuraFilters,
} from '../types/estructura.types';

export async function getCarrerasAdmin(filters?: EstructuraFilters): Promise<Carrera[]> {
  const { data } = await api.get<Carrera[] | Paginated<Carrera>>('/api/v1/admin/carreras', { params: filters });
  return toList(data);
}

export async function crearCarreraAdmin(payload: CarreraCreate): Promise<Carrera> {
  const { data } = await api.post<Carrera>('/api/v1/admin/carreras', payload);
  return data;
}

export async function actualizarCarreraAdmin(id: string, payload: Partial<CarreraCreate>): Promise<Carrera> {
  const { data } = await api.put<Carrera>(`/api/v1/admin/carreras/${id}`, payload);
  return data;
}

export async function getCohortesAdmin(filters?: EstructuraFilters): Promise<Cohorte[]> {
  const { data } = await api.get<Cohorte[] | Paginated<Cohorte>>('/api/v1/admin/cohortes', { params: filters });
  return toList(data);
}

export async function crearCohorteAdmin(payload: CohorteCreate): Promise<Cohorte> {
  const { data } = await api.post<Cohorte>('/api/v1/admin/cohortes', payload);
  return data;
}

export async function actualizarCohorteAdmin(id: string, payload: Partial<CohorteCreate>): Promise<Cohorte> {
  const { data } = await api.put<Cohorte>(`/api/v1/admin/cohortes/${id}`, payload);
  return data;
}

export async function getMateriasAdmin(filters?: EstructuraFilters): Promise<Materia[]> {
  const { data } = await api.get<Materia[] | Paginated<Materia>>('/api/v1/admin/materias', { params: filters });
  return toList(data);
}

export async function crearMateriaAdmin(payload: MateriaCreate): Promise<Materia> {
  const { data } = await api.post<Materia>('/api/v1/admin/materias', payload);
  return data;
}

export async function actualizarMateriaAdmin(id: string, payload: Partial<MateriaCreate>): Promise<Materia> {
  const { data } = await api.put<Materia>(`/api/v1/admin/materias/${id}`, payload);
  return data;
}
