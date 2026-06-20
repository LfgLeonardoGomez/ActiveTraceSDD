import api from '@/shared/services/api';
import type { Factura, FacturaCreate, FacturaFilters } from '../types/facturas.types';

// GET /api/v1/facturas — returns { items, total, page, page_size }
export async function getFacturas(filters?: FacturaFilters): Promise<{ items: Factura[]; total: number; page: number; page_size: number }> {
  const { data } = await api.get('/api/v1/facturas', { params: filters });
  return data;
}

// POST /api/v1/facturas — body: FacturaCreate (usuario_id, periodo, detalle?, referencia_archivo, tamano_kb?)
export async function crearFactura(payload: FacturaCreate): Promise<Factura> {
  const { data } = await api.post<Factura>('/api/v1/facturas', payload);
  return data;
}

// POST /api/v1/facturas/{id}/abonar — no body
export async function abonarFactura(id: string): Promise<Factura> {
  const { data } = await api.post<Factura>(`/api/v1/facturas/${id}/abonar`);
  return data;
}

// DELETE /api/v1/facturas/{id} — 204 No Content
export async function eliminarFactura(id: string): Promise<void> {
  await api.delete(`/api/v1/facturas/${id}`);
}
