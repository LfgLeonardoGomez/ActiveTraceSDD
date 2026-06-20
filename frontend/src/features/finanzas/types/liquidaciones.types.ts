import { z } from 'zod';

export const PeriodoSchema = z.object({
  cohorte_id: z.string().uuid(),
  periodo: z.string().regex(/^\d{4}-\d{2}$/),
});

// Aligned to backend CerrarLiquidacionRequest schema (liquidaciones/schemas/liquidacion.py)
export const CerrarLiquidacionSchema = z.object({
  confirmar_cierre: z.literal(true),
  periodo: z.string(),
});

// Aligned to backend LiquidacionFilaRead schema (liquidaciones/schemas/liquidacion.py)
export const LiquidacionItemSchema = z.object({
  id: z.string().uuid().nullable().optional(),
  usuario_id: z.string().uuid(),
  rol: z.string(),
  monto_base: z.number().nonnegative(),
  monto_plus: z.number().nonnegative(),
  total: z.number().nonnegative(),
  es_nexo: z.boolean(),
  excluido_por_factura: z.boolean(),
  estado: z.string(),
  cerrada_at: z.string().datetime().nullable().optional(),
  cerrada_por_usuario_id: z.string().uuid().nullable().optional(),
  plus_detalle: z.array(z.object({
    grupo: z.string(),
    monto_unitario: z.number(),
    n_comisiones_detectadas: z.number().int(),
    n_comisiones_acumuladas: z.number().int(),
    tope_acumulacion: z.number().nullable(),
    subtotal: z.number(),
  })).default([]),
});

// Aligned to backend LiquidacionPeriodoResponse schema (liquidaciones/schemas/liquidacion.py)
export const LiquidacionViewSchema = z.object({
  cohorte_id: z.string().uuid(),
  periodo: z.string(),
  estado: z.string(),
  cerrada_at: z.string().datetime().nullable().optional(),
  cerrada_por_usuario_id: z.string().uuid().nullable().optional(),
  segmentos: z.object({
    general: z.array(LiquidacionItemSchema).default([]),
    nexo: z.array(LiquidacionItemSchema).default([]),
    facturantes: z.array(LiquidacionItemSchema).default([]),
  }),
  total_sin_factura: z.number().nonnegative(),
  total_con_factura: z.number().nonnegative(),
  warnings: z.array(z.object({
    usuario_id: z.string().uuid(),
    rol: z.string(),
    motivo: z.string(),
  })).default([]),
});

// Aligned to backend HistorialResponse / HistorialPeriodoItem (liquidaciones/schemas/liquidacion.py)
export const HistorialFiltersSchema = z.object({
  cohorte_id: z.string().uuid().optional(),
  usuario_id: z.string().uuid().optional(),
  desde: z.string().regex(/^\d{4}-\d{2}$/).optional(),
  hasta: z.string().regex(/^\d{4}-\d{2}$/).optional(),
  page: z.number().int().positive().default(1),
  page_size: z.number().int().positive().default(20),
}).strict();

export type Periodo = z.infer<typeof PeriodoSchema>;
export type CerrarLiquidacion = z.infer<typeof CerrarLiquidacionSchema>;
export type LiquidacionItem = z.infer<typeof LiquidacionItemSchema>;
export type LiquidacionView = z.infer<typeof LiquidacionViewSchema>;
export type HistorialFilters = z.infer<typeof HistorialFiltersSchema>;

// Aligned to backend HistorialPeriodoItem (liquidaciones/schemas/liquidacion.py)
export interface LiquidacionHistorialEntry {
  cohorte_id: string;
  periodo: string;
  total_filas: number;
  total_sin_factura: number;
  total_con_factura: number;
  cerrada_at: string;
  cerrada_por_usuario_id: string;
}
