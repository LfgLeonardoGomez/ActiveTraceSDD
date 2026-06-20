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

// ---------------------------------------------------------------------------
// Raw API shapes (backend schemas/estructura.py)
// ---------------------------------------------------------------------------

// CarreraRead: { id, tenant_id, codigo, nombre, estado, created_at?, updated_at?, deleted_at? }
// API estado values: "Activa" | "Inactiva" — view model uses "activo" | "inactivo"
interface CarreraApiItem {
  id: string;
  tenant_id: string;
  codigo: string;
  nombre: string;
  estado: string;
  created_at: string | null;
  updated_at: string | null;
  deleted_at: string | null;
}

// CohorteRead: { id, tenant_id, carrera_id, nombre, anio, vig_desde, vig_hasta?, estado, created_at?, updated_at? }
// View model expects: { id, nombre, anio, vigencia_desde, vigencia_hasta, estado, carrera_id, carrera_nombre? }
interface CohorteApiItem {
  id: string;
  tenant_id: string;
  carrera_id: string;
  nombre: string;
  anio: number;
  vig_desde: string;
  vig_hasta: string | null;
  estado: string;
  created_at: string | null;
  updated_at: string | null;
  deleted_at: string | null;
}

// MateriaRead: { id, tenant_id, codigo, nombre, estado, created_at?, updated_at?, deleted_at? }
interface MateriaApiItem {
  id: string;
  tenant_id: string;
  codigo: string;
  nombre: string;
  estado: string;
  created_at: string | null;
  updated_at: string | null;
  deleted_at: string | null;
}

// ---------------------------------------------------------------------------
// Mapping — normalise backend "Activa"/"Inactiva" → "activo"/"inactivo"
// ---------------------------------------------------------------------------

function normaliseEstado(estado: string): 'activo' | 'inactivo' {
  return estado.toLowerCase().startsWith('activ') ? 'activo' : 'inactivo';
}

function mapCarreraApiToView(item: CarreraApiItem): Carrera {
  return {
    id: item.id,
    nombre: item.nombre,
    codigo: item.codigo,
    estado: normaliseEstado(item.estado),
    created_at: item.created_at ?? undefined,
    updated_at: item.updated_at ?? undefined,
  };
}

function mapCohorteApiToView(item: CohorteApiItem): Cohorte {
  return {
    id: item.id,
    nombre: item.nombre,
    anio: item.anio,
    vigencia_desde: item.vig_desde,
    vigencia_hasta: item.vig_hasta ?? '',
    estado: normaliseEstado(item.estado),
    carrera_id: item.carrera_id,
    created_at: item.created_at ?? undefined,
    updated_at: item.updated_at ?? undefined,
  };
}

function mapMateriaApiToView(item: MateriaApiItem): Materia {
  return {
    id: item.id,
    nombre: item.nombre,
    codigo: item.codigo,
    estado: normaliseEstado(item.estado),
    created_at: item.created_at ?? undefined,
    updated_at: item.updated_at ?? undefined,
  };
}

// ---------------------------------------------------------------------------
// Service functions
// ---------------------------------------------------------------------------

export async function getCarrerasAdmin(filters?: EstructuraFilters): Promise<Carrera[]> {
  const { data } = await api.get<CarreraApiItem[] | Paginated<CarreraApiItem>>('/api/v1/admin/carreras', { params: filters });
  return toList(data).map(mapCarreraApiToView);
}

export async function crearCarreraAdmin(payload: CarreraCreate): Promise<Carrera> {
  const { data } = await api.post<CarreraApiItem>('/api/v1/admin/carreras', payload);
  return mapCarreraApiToView(data);
}

export async function actualizarCarreraAdmin(id: string, payload: Partial<CarreraCreate>): Promise<Carrera> {
  const { data } = await api.put<CarreraApiItem>(`/api/v1/admin/carreras/${id}`, payload);
  return mapCarreraApiToView(data);
}

export async function getCohortesAdmin(filters?: EstructuraFilters): Promise<Cohorte[]> {
  const { data } = await api.get<CohorteApiItem[] | Paginated<CohorteApiItem>>('/api/v1/admin/cohortes', { params: filters });
  return toList(data).map(mapCohorteApiToView);
}

export async function crearCohorteAdmin(payload: CohorteCreate): Promise<Cohorte> {
  const { data } = await api.post<CohorteApiItem>('/api/v1/admin/cohortes', payload);
  return mapCohorteApiToView(data);
}

export async function actualizarCohorteAdmin(id: string, payload: Partial<CohorteCreate>): Promise<Cohorte> {
  const { data } = await api.put<CohorteApiItem>(`/api/v1/admin/cohortes/${id}`, payload);
  return mapCohorteApiToView(data);
}

export async function getMateriasAdmin(filters?: EstructuraFilters): Promise<Materia[]> {
  const { data } = await api.get<MateriaApiItem[] | Paginated<MateriaApiItem>>('/api/v1/admin/materias', { params: filters });
  return toList(data).map(mapMateriaApiToView);
}

export async function crearMateriaAdmin(payload: MateriaCreate): Promise<Materia> {
  const { data } = await api.post<MateriaApiItem>('/api/v1/admin/materias', payload);
  return mapMateriaApiToView(data);
}

export async function actualizarMateriaAdmin(id: string, payload: Partial<MateriaCreate>): Promise<Materia> {
  const { data } = await api.put<MateriaApiItem>(`/api/v1/admin/materias/${id}`, payload);
  return mapMateriaApiToView(data);
}
