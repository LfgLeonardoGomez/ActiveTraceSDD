import { z } from 'zod';

export const SalarioBaseSchema = z
  .object({
    id: z.string().uuid(),
    rol: z.string().min(1),
    monto: z.number().positive(),
    vigencia_desde: z.string().date(),
    vigencia_hasta: z.string().date(),
  })
  .strict();

export const SalarioBaseCreateSchema = z
  .object({
    rol: z.string().min(1),
    monto: z.number().positive(),
    vigencia_desde: z.string().date(),
    vigencia_hasta: z.string().date(),
  })
  .strict();

export const SalarioPlusSchema = z
  .object({
    id: z.string().uuid(),
    grupo: z.string().min(1),
    rol: z.string().min(1),
    monto: z.number().positive(),
    vigencia_desde: z.string().date(),
    vigencia_hasta: z.string().date(),
  })
  .strict();

export const SalarioPlusCreateSchema = z
  .object({
    grupo: z.string().min(1),
    rol: z.string().min(1),
    monto: z.number().positive(),
    vigencia_desde: z.string().date(),
    vigencia_hasta: z.string().date(),
  })
  .strict();

export const SalarioFiltersSchema = z
  .object({
    rol: z.string().optional(),
    vigencia_activa: z.boolean().optional(),
  })
  .strict();

export type SalarioBase = z.infer<typeof SalarioBaseSchema>;
export type SalarioBaseCreate = z.infer<typeof SalarioBaseCreateSchema>;
export type SalarioPlus = z.infer<typeof SalarioPlusSchema>;
export type SalarioPlusCreate = z.infer<typeof SalarioPlusCreateSchema>;
export type SalarioFilters = z.infer<typeof SalarioFiltersSchema>;
