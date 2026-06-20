import { z } from 'zod';

// Aligned to backend SalarioBaseRead schema (liquidaciones/schemas/salario_base.py)
export const SalarioBaseSchema = z
  .object({
    id: z.string().uuid(),
    tenant_id: z.string().uuid(),
    rol: z.string().min(1),
    monto: z.number().positive(),
    desde: z.string().date(),
    hasta: z.string().date().nullable(),
  });

// Aligned to backend SalarioBaseCreate schema (liquidaciones/schemas/salario_base.py)
export const SalarioBaseCreateSchema = z
  .object({
    rol: z.string().min(1),
    monto: z.number().positive(),
    desde: z.string().date(),
    hasta: z.string().date().optional(),
  })
  .strict();

// Aligned to backend SalarioPlusRead schema (liquidaciones/schemas/salario_plus.py)
export const SalarioPlusSchema = z
  .object({
    id: z.string().uuid(),
    tenant_id: z.string().uuid(),
    grupo: z.string().min(1),
    rol: z.string().min(1),
    descripcion: z.string().nullable(),
    monto: z.number().positive(),
    tope_acumulacion: z.number().nullable(),
    desde: z.string().date(),
    hasta: z.string().date().nullable(),
  });

// Aligned to backend SalarioPlusCreate schema (liquidaciones/schemas/salario_plus.py)
export const SalarioPlusCreateSchema = z
  .object({
    grupo: z.string().min(1),
    rol: z.string().min(1),
    descripcion: z.string().optional(),
    monto: z.number().positive(),
    tope_acumulacion: z.number().optional(),
    desde: z.string().date(),
    hasta: z.string().date().optional(),
  })
  .strict();

export const SalarioFiltersSchema = z
  .object({
    rol: z.string().optional(),
  })
  .strict();

export type SalarioBase = z.infer<typeof SalarioBaseSchema>;
export type SalarioBaseCreate = z.infer<typeof SalarioBaseCreateSchema>;
export type SalarioPlus = z.infer<typeof SalarioPlusSchema>;
export type SalarioPlusCreate = z.infer<typeof SalarioPlusCreateSchema>;
export type SalarioFilters = z.infer<typeof SalarioFiltersSchema>;
