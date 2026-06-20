import { z } from 'zod';

// Aligned to backend FacturaRead schema (liquidaciones/schemas/factura.py)
export const FacturaSchema = z
  .object({
    id: z.string().uuid(),
    tenant_id: z.string().uuid(),
    usuario_id: z.string().uuid(),
    periodo: z.string(),
    detalle: z.string().nullable(),
    referencia_archivo: z.string(),
    tamano_kb: z.number().nullable(),
    estado: z.string(),
    cargada_at: z.string().datetime(),
    abonada_at: z.string().datetime().nullable(),
  });

// Aligned to backend FacturaCreate schema (liquidaciones/schemas/factura.py)
export const FacturaCreateSchema = z
  .object({
    usuario_id: z.string().uuid(),
    periodo: z.string(),
    detalle: z.string().optional(),
    referencia_archivo: z.string(),
    tamano_kb: z.number().optional(),
  })
  .strict();

// Aligned to backend FacturaListFilter schema (liquidaciones/schemas/factura.py)
export const FacturaFiltersSchema = z
  .object({
    usuario_id: z.string().uuid().optional(),
    estado: z.string().optional(),
    desde: z.string().optional(),
    hasta: z.string().optional(),
    q: z.string().optional(),
    page: z.number().int().positive().default(1),
    page_size: z.number().int().positive().default(20),
  })
  .strict();

export type Factura = z.infer<typeof FacturaSchema>;
export type FacturaCreate = z.infer<typeof FacturaCreateSchema>;
export type FacturaFilters = z.infer<typeof FacturaFiltersSchema>;
