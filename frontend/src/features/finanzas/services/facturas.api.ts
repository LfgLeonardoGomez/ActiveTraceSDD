import api from '@/shared/services/api';
import type { Factura, FacturaCreate, FacturaFilters } from '../types/facturas.types';

export async function getFacturas(filters?: FacturaFilters): Promise<{ items: Factura[]; total: number }> {
  const { data } = await api.get('/api/facturas', { params: filters });
  return data;
}

export async function crearFactura(payload: FacturaCreate): Promise<Factura> {
  const { data } = await api.post<Factura>('/api/facturas', payload);
  return data;
}

export async function abonarFactura(id: string): Promise<Factura> {
  const { data } = await api.post<Factura>(`/api/facturas/${id}/abonar`);
  return data;
}

export async function eliminarFactura(id: string): Promise<void> {
  await api.delete(`/api/facturas/${id}`);
}
