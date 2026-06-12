import { z } from 'zod';

export const UsuarioSchema = z
  .object({
    id: z.string().uuid(),
    nombre: z.string().min(1),
    email: z.string().email(),
    roles: z.array(z.string()),
    estado: z.enum(['activo', 'inactivo', 'pendiente']),
    dni: z.string().optional(),
    cuil: z.string().optional(),
    cbu: z.string().optional(),
    banco: z.string().optional(),
    regional: z.string().optional(),
    created_at: z.string().datetime().optional(),
    updated_at: z.string().datetime().optional(),
  })
  .strict();

export const UsuarioUpdateSchema = z
  .object({
    nombre: z.string().min(1).optional(),
    email: z.string().email().optional(),
    regional: z.string().optional(),
    banco: z.string().optional(),
    estado: z.enum(['activo', 'inactivo', 'pendiente']).optional(),
  })
  .strict();

export const UsuarioFiltersSchema = z
  .object({
    nombre: z.string().optional(),
    email: z.string().optional(),
    rol: z.string().optional(),
    estado: z.enum(['activo', 'inactivo', 'pendiente']).optional(),
  })
  .strict();

export type Usuario = z.infer<typeof UsuarioSchema>;
export type UsuarioUpdate = z.infer<typeof UsuarioUpdateSchema>;
export type UsuarioFilters = z.infer<typeof UsuarioFiltersSchema>;
