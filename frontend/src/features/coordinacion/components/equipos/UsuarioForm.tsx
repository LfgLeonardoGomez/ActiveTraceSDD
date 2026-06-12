import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { useCrearUsuario, useActualizarUsuario } from '../../hooks/useEquipos';
import type { UsuarioDocente } from '../../types/equipos.types';

const schema = z.object({
  nombre: z.string().min(1, 'Nombre requerido'),
  email: z.string().email('Email inválido'),
  rol: z.enum(['PROFESOR', 'TUTOR', 'NEXO', 'COORDINADOR'], { errorMap: () => ({ message: 'Rol inválido' }) }),
  regional: z.string().min(1, 'Regional requerida'),
  activo: z.boolean(),
});

type FormValues = z.infer<typeof schema>;

const ROLES = ['PROFESOR', 'TUTOR', 'NEXO', 'COORDINADOR'] as const;

interface UsuarioFormProps {
  usuario?: UsuarioDocente | null;
  onSuccess?: () => void;
}

export function UsuarioForm({ usuario, onSuccess }: UsuarioFormProps) {
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const crearMutation = useCrearUsuario();
  const actualizarMutation = useActualizarUsuario();
  const isEdit = !!usuario;

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      nombre: '',
      email: '',
      rol: 'PROFESOR',
      regional: '',
      activo: true,
    },
  });

  useEffect(() => {
    if (usuario) {
      reset({
        nombre: usuario.nombre,
        email: usuario.email,
        rol: usuario.rol as FormValues['rol'],
        regional: usuario.regional,
        activo: usuario.activo,
      });
    }
  }, [usuario, reset]);

  const onSubmit = async (values: FormValues) => {
    setMessage(null);
    try {
      if (isEdit && usuario) {
        await actualizarMutation.mutateAsync({ id: usuario.id, data: values });
        setMessage({ type: 'success', text: 'Usuario actualizado correctamente' });
      } else {
        await crearMutation.mutateAsync(values);
        setMessage({ type: 'success', text: 'Usuario creado correctamente' });
      }
      onSuccess?.();
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 409) {
        setMessage({ type: 'error', text: 'El email ya está registrado' });
      } else {
        setMessage({ type: 'error', text: `Error al ${isEdit ? 'actualizar' : 'crear'} el usuario` });
      }
    }
  };

  const isPending = crearMutation.isPending || actualizarMutation.isPending;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{isEdit ? 'Editar Usuario' : 'Nuevo Usuario'}</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Nombre"
            {...register('nombre')}
            error={errors.nombre?.message}
          />
          <Input
            label="Email"
            type="email"
            {...register('email')}
            error={errors.email?.message}
          />
          <div className="space-y-2">
            <label className="text-sm font-medium text-neutral-700">Rol</label>
            <select
              {...register('rol')}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              {ROLES.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
            {errors.rol && <p className="text-sm text-danger-600">{errors.rol.message}</p>}
          </div>
          <Input
            label="Regional"
            {...register('regional')}
            error={errors.regional?.message}
          />
          <div className="flex items-center gap-2">
            <input type="checkbox" id="activo" {...register('activo')} className="rounded border-neutral-300" />
            <label htmlFor="activo" className="text-sm font-medium text-neutral-700">Activo</label>
          </div>

          {message && (
            <div
              className={`rounded-md p-3 text-sm ${
                message.type === 'success' ? 'bg-success-50 text-success-600' : 'bg-danger-50 text-danger-600'
              }`}
            >
              {message.text}
            </div>
          )}

          <Button type="submit" isLoading={isPending} disabled={isPending}>
            {isPending
              ? isEdit ? 'Actualizando...' : 'Creando...'
              : isEdit ? 'Actualizar usuario' : 'Crear usuario'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
