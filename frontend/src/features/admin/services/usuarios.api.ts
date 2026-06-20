import api from '@/shared/services/api';
import type { Usuario, UsuarioUpdate, UsuarioFilters } from '../types/usuarios.types';

// Raw shape returned by GET /api/v1/admin/usuarios (UsuarioListRead — PII masked)
interface UsuarioListApiItem {
  id: string;
  tenant_id: string;
  nombre: string;
  apellidos: string;
  email: string;
  estado: string;
  legajo: string | null;
  dni: string | null;
  cuil: string | null;
  banco: string | null;
  regional: string | null;
  legajo_profesional: string | null;
  facturador: boolean | null;
}

interface PaginatedUsuariosApiResponse {
  items: UsuarioListApiItem[];
  total: number;
  limit: number;
  offset: number;
}

function mapUsuarioApiToView(item: UsuarioListApiItem): Usuario {
  return {
    id: item.id,
    nombre: `${item.nombre} ${item.apellidos}`.trim(),
    email: item.email,
    // roles are not returned by the list endpoint; default to empty array
    roles: [],
    estado: item.estado as Usuario['estado'],
    dni: item.dni ?? undefined,
    cuil: item.cuil ?? undefined,
    // cbu is omitted in the list response (PII — only in detail)
    cbu: undefined,
    banco: item.banco ?? undefined,
    regional: item.regional ?? undefined,
  };
}

export async function getUsuariosAdmin(filters?: UsuarioFilters): Promise<{ items: Usuario[]; total: number }> {
  const { data } = await api.get<PaginatedUsuariosApiResponse>('/api/v1/admin/usuarios', { params: filters });
  return {
    items: data.items.map(mapUsuarioApiToView),
    total: data.total,
  };
}

export async function actualizarUsuarioAdmin(id: string, payload: UsuarioUpdate): Promise<Usuario> {
  const { data } = await api.patch<UsuarioListApiItem>(`/api/v1/admin/usuarios/${id}`, payload);
  return mapUsuarioApiToView(data);
}
