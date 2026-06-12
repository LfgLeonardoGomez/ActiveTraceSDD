import { z } from 'zod';

export const PeriodoSchema = z.object({
  cohorte_id: z.string().uuid(),
  mes: z.string().regex(/^\d{4}-\d{2}$/),
});

export const CerrarLiquidacionSchema = z.object({
  confirmado: z.literal(true),
});

export const LiquidacionItemSchema = z.object({
  docente_id: z.string().uuid(),
  docente_nombre: z.string(),
  rol: z.string(),
  salario_base: z.number().nonnegative(),
  salario_plus: z.number().nonnegative(),
  comisiones: z.number().nonnegative(),
  total: z.number().nonnegative(),
  es_facturante: z.boolean().optional(),
  es_nexo: z.boolean().optional(),
});

export const LiquidacionViewSchema = z.object({
  periodo: z.string(),
  estado: z.enum(['abierto', 'cerrado']),
  segmento_general: z.array(LiquidacionItemSchema),
  segmento_nexo: z.array(LiquidacionItemSchema),
  segmento_facturantes: z.array(LiquidacionItemSchema),
  total_sin_factura: z.number().nonnegative(),
  total_con_factura: z.number().nonnegative(),
});

export const HistorialFiltersSchema = z.object({
  cohorte_id: z.string().uuid().optional(),
  mes: z.string().regex(/^\d{4}-\d{2}$/).optional(),
  estado: z.enum(['abierto', 'cerrado']).optional(),
  page: z.number().int().positive().default(1),
  page_size: z.number().int().positive().default(50),
}).strict();

export type Periodo = z.infer<typeof PeriodoSchema>;
export type CerrarLiquidacion = z.infer<typeof CerrarLiquidacionSchema>;
export type LiquidacionItem = z.infer<typeof LiquidacionItemSchema>;
export type LiquidacionView = z.infer<typeof LiquidacionViewSchema>;
export type HistorialFilters = z.infer<typeof HistorialFiltersSchema>;

export interface LiquidacionHistorialEntry {
  id: string;
  periodo: string;
  cohorte_id: string;
  cohorte_nombre: string;
  estado: 'abierto' | 'cerrado';
  total_sin_factura: number;
  total_con_factura: number;
  fecha_cierre?: string;
}
