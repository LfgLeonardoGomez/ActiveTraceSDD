import { z } from 'zod';

export const CarreraSchema = z
  .object({
    id: z.string().uuid(),
    nombre: z.string().min(1),
    codigo: z.string().min(1),
    estado: z.enum(['activo', 'inactivo']),
    created_at: z.string().datetime().optional(),
    updated_at: z.string().datetime().optional(),
  })
  .strict();

export const CarreraCreateSchema = z
  .object({
    nombre: z.string().min(1),
    codigo: z.string().min(1),
    estado: z.enum(['activo', 'inactivo']).default('activo'),
  })
  .strict();

export const CohorteSchema = z
  .object({
    id: z.string().uuid(),
    nombre: z.string().min(1),
    anio: z.number().int().positive(),
    vigencia_desde: z.string().date(),
    vigencia_hasta: z.string().date(),
    estado: z.enum(['activo', 'inactivo']),
    carrera_id: z.string().uuid(),
    carrera_nombre: z.string().optional(),
    created_at: z.string().datetime().optional(),
    updated_at: z.string().datetime().optional(),
  })
  .strict();

export const CohorteCreateSchema = z
  .object({
    nombre: z.string().min(1),
    anio: z.number().int().positive(),
    vigencia_desde: z.string().date(),
    vigencia_hasta: z.string().date(),
    estado: z.enum(['activo', 'inactivo']).default('activo'),
    carrera_id: z.string().uuid(),
  })
  .strict();

export const MateriaSchema = z
  .object({
    id: z.string().uuid(),
    nombre: z.string().min(1),
    codigo: z.string().min(1),
    estado: z.enum(['activo', 'inactivo']),
    created_at: z.string().datetime().optional(),
    updated_at: z.string().datetime().optional(),
  })
  .strict();

export const MateriaCreateSchema = z
  .object({
    nombre: z.string().min(1),
    codigo: z.string().min(1),
    estado: z.enum(['activo', 'inactivo']).default('activo'),
  })
  .strict();

export const EstructuraFiltersSchema = z
  .object({
    nombre: z.string().optional(),
    estado: z.enum(['activo', 'inactivo']).optional(),
  })
  .strict();

export type Carrera = z.infer<typeof CarreraSchema>;
export type CarreraCreate = z.infer<typeof CarreraCreateSchema>;
export type Cohorte = z.infer<typeof CohorteSchema>;
export type CohorteCreate = z.infer<typeof CohorteCreateSchema>;
export type Materia = z.infer<typeof MateriaSchema>;
export type MateriaCreate = z.infer<typeof MateriaCreateSchema>;
export type EstructuraFilters = z.infer<typeof EstructuraFiltersSchema>;
