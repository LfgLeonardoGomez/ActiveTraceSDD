import { z } from 'zod';

export const FacturaSchema = z
  .object({
    id: z.string().uuid(),
    docente_id: z.string().uuid(),
    docente_nombre: z.string(),
    periodo: z.string(),
    monto: z.number().positive(),
    estado: z.enum(['pendiente', 'abonada', 'cancelada']),
    fecha_subida: z.string().datetime(),
    fecha_pago: z.string().datetime().optional(),
    archivo_url: z.string().url().optional(),
  })
  .strict();

export const FacturaCreateSchema = z
  .object({
    docente_id: z.string().uuid(),
    periodo: z.string(),
    monto: z.number().positive(),
    archivo: z.instanceof(File).optional(),
  })
  .strict();

export const FacturaFiltersSchema = z
  .object({
    docente_id: z.string().uuid().optional(),
    periodo: z.string().optional(),
    estado: z.enum(['pendiente', 'abonada', 'cancelada']).optional(),
    page: z.number().int().positive().default(1),
    page_size: z.number().int().positive().default(50),
  })
  .strict();

export type Factura = z.infer<typeof FacturaSchema>;
export type FacturaCreate = z.infer<typeof FacturaCreateSchema>;
export type FacturaFilters = z.infer<typeof FacturaFiltersSchema>;
