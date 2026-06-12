import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import type { Usuario, UsuarioUpdate } from '../../types/usuarios.types';

const schema = z.object({
  nombre: z.string().min(1, 'El nombre es obligatorio').optional(),
  email: z.string().email('Email inválido').optional(),
  regional: z.string().optional(),
  banco: z.string().optional(),
  estado: z.enum(['activo', 'inactivo', 'pendiente']).optional(),
});

type FormData = z.infer<typeof schema>;

interface UsuarioFormProps {
  user?: Usuario | null;
  onSubmit: (data: UsuarioUpdate) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export default function UsuarioForm({ user, onSubmit, onCancel, isLoading }: UsuarioFormProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      nombre: '',
      email: '',
      regional: '',
      banco: '',
      estado: 'activo',
    },
  });

  useEffect(() => {
    if (user) {
      reset({
        nombre: user.nombre,
        email: user.email,
        regional: user.regional ?? '',
        banco: user.banco ?? '',
        estado: user.estado,
      });
    } else {
      reset({ nombre: '', email: '', regional: '', banco: '', estado: 'activo' });
    }
  }, [user, reset]);

  const handleFormSubmit = (data: FormData) => {
    onSubmit(data as UsuarioUpdate);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Editar usuario</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
          <Input label="Nombre" error={errors.nombre?.message} {...register('nombre')} />
          <Input label="Email" type="email" error={errors.email?.message} {...register('email')} />
          <Input label="Regional" {...register('regional')} />
          <Input label="Banco" {...register('banco')} />
          <div className="space-y-2">
            <label className="text-sm font-medium">Estado</label>
            <select
              {...register('estado')}
              className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
            >
              <option value="activo">Activo</option>
              <option value="inactivo">Inactivo</option>
              <option value="pendiente">Pendiente</option>
            </select>
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>
              Cancelar
            </Button>
            <Button type="submit" isLoading={isLoading}>
              Guardar cambios
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
