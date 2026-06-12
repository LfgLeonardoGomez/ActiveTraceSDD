import { z } from 'zod';

export const AuditLogFiltersSchema = z
  .object({
    fecha_desde: z.string().date().optional(),
    fecha_hasta: z.string().date().optional(),
    accion: z.string().optional(),
    usuario_id: z.string().uuid().optional(),
    materia_id: z.string().uuid().optional(),
    estado: z.string().optional(),
    page: z.number().int().positive().default(1),
    page_size: z.number().int().positive().default(50),
  })
  .strict();

export const AccionPorDiaSchema = z
  .object({
    fecha: z.string().date(),
    cantidad: z.number().int().nonnegative(),
  })
  .strict();

export const ComunicacionPorDocenteSchema = z
  .object({
    docente_id: z.string().uuid(),
    docente_nombre: z.string(),
    enviadas: z.number().int().nonnegative(),
    pendientes: z.number().int().nonnegative(),
    fallidas: z.number().int().nonnegative(),
  })
  .strict();

export const InteraccionPorDocenteMateriaSchema = z
  .object({
    docente_id: z.string().uuid(),
    docente_nombre: z.string(),
    materia_id: z.string().uuid(),
    materia_nombre: z.string(),
    interacciones: z.number().int().nonnegative(),
  })
  .strict();

export const AuditLogEntrySchema = z
  .object({
    id: z.string().uuid(),
    timestamp: z.string().datetime(),
    usuario_id: z.string().uuid(),
    usuario_nombre: z.string(),
    accion: z.string(),
    modulo: z.string(),
    descripcion: z.string(),
    materia_id: z.string().uuid().optional(),
    materia_nombre: z.string().optional(),
    estado: z.string(),
  })
  .strict();

export const UltimaAccionSchema = z
  .object({
    id: z.string().uuid(),
    timestamp: z.string().datetime(),
    usuario_nombre: z.string(),
    accion: z.string(),
    modulo: z.string(),
    descripcion: z.string(),
  })
  .strict();

export const CatalogoAccionSchema = z
  .object({
    codigo: z.string(),
    descripcion: z.string(),
  })
  .strict();

export type AuditLogFilters = z.infer<typeof AuditLogFiltersSchema>;
export type AccionPorDia = z.infer<typeof AccionPorDiaSchema>;
export type ComunicacionPorDocente = z.infer<typeof ComunicacionPorDocenteSchema>;
export type InteraccionPorDocenteMateria = z.infer<typeof InteraccionPorDocenteMateriaSchema>;
export type AuditLogEntry = z.infer<typeof AuditLogEntrySchema>;
export type UltimaAccion = z.infer<typeof UltimaAccionSchema>;
export type CatalogoAccion = z.infer<typeof CatalogoAccionSchema>;
