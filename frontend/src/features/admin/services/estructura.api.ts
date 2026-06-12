import api from '@/shared/services/api';
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
  const { data } = await api.get<Carrera[]>('/api/admin/carreras', { params: filters });
  return data;
}

export async function crearCarreraAdmin(payload: CarreraCreate): Promise<Carrera> {
  const { data } = await api.post<Carrera>('/api/admin/carreras', payload);
  return data;
}

export async function actualizarCarreraAdmin(id: string, payload: Partial<CarreraCreate>): Promise<Carrera> {
  const { data } = await api.patch<Carrera>(`/api/admin/carreras/${id}`, payload);
  return data;
}

export async function getCohortesAdmin(filters?: EstructuraFilters): Promise<Cohorte[]> {
  const { data } = await api.get<Cohorte[]>('/api/admin/cohortes', { params: filters });
  return data;
}

export async function crearCohorteAdmin(payload: CohorteCreate): Promise<Cohorte> {
  const { data } = await api.post<Cohorte>('/api/admin/cohortes', payload);
  return data;
}

export async function actualizarCohorteAdmin(id: string, payload: Partial<CohorteCreate>): Promise<Cohorte> {
  const { data } = await api.patch<Cohorte>(`/api/admin/cohortes/${id}`, payload);
  return data;
}

export async function getMateriasAdmin(filters?: EstructuraFilters): Promise<Materia[]> {
  const { data } = await api.get<Materia[]>('/api/admin/materias', { params: filters });
  return data;
}

export async function crearMateriaAdmin(payload: MateriaCreate): Promise<Materia> {
  const { data } = await api.post<Materia>('/api/admin/materias', payload);
  return data;
}

export async function actualizarMateriaAdmin(id: string, payload: Partial<MateriaCreate>): Promise<Materia> {
  const { data } = await api.patch<Materia>(`/api/admin/materias/${id}`, payload);
  return data;
}
