import { useState } from 'react';
import { Card, CardContent } from '@/shared/components/ui/Card';
import { Input } from '@/shared/components/ui/Input';
import { Spinner } from '@/shared/components/ui/Spinner';
import { useUsuariosAdmin, useActualizarUsuarioAdmin } from '../hooks/useUsuarios';
import UsuarioTable from '../components/usuarios/UsuarioTable';
import UsuarioDetail from '../components/usuarios/UsuarioDetail';
import UsuarioForm from '../components/usuarios/UsuarioForm';
import type { Usuario, UsuarioFilters, UsuarioUpdate } from '../types/usuarios.types';

export default function UsuariosPage() {
  const [filters, setFilters] = useState<UsuarioFilters>({});
  const [detailUser, setDetailUser] = useState<Usuario | null>(null);
  const [editingUser, setEditingUser] = useState<Usuario | null>(null);
  const [showForm, setShowForm] = useState(false);

  const { data, isLoading } = useUsuariosAdmin(filters);
  const actualizar = useActualizarUsuarioAdmin();

  const handleFilterChange = (key: keyof UsuarioFilters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value || undefined }));
  };

  const handleEdit = (user: Usuario) => {
    setEditingUser(user);
    setShowForm(true);
  };

  const handleUpdate = (data: UsuarioUpdate) => {
    if (!editingUser) return;
    actualizar.mutate(
      { id: editingUser.id, data },
      {
        onSuccess: () => {
          setShowForm(false);
          setEditingUser(null);
        },
      },
    );
  };

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold tracking-tight">Usuarios</h1>

      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-3">
            <Input
              label="Nombre"
              placeholder="Buscar por nombre..."
              value={filters.nombre ?? ''}
              onChange={(e) => handleFilterChange('nombre', e.target.value)}
              className="w-56"
            />
            <Input
              label="Email"
              placeholder="Buscar por email..."
              value={filters.email ?? ''}
              onChange={(e) => handleFilterChange('email', e.target.value)}
              className="w-56"
            />
            <Input
              label="Rol"
              placeholder="Buscar por rol..."
              value={filters.rol ?? ''}
              onChange={(e) => handleFilterChange('rol', e.target.value)}
              className="w-40"
            />
            <div className="space-y-2">
              <label className="text-sm font-medium">Estado</label>
              <select
                value={filters.estado ?? ''}
                onChange={(e) => handleFilterChange('estado', e.target.value)}
                className="h-10 w-40 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
              >
                <option value="">Todos</option>
                <option value="activo">Activo</option>
                <option value="inactivo">Inactivo</option>
                <option value="pendiente">Pendiente</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {showForm && (
        <UsuarioForm
          user={editingUser}
          onSubmit={handleUpdate}
          onCancel={() => {
            setShowForm(false);
            setEditingUser(null);
          }}
          isLoading={actualizar.isPending}
        />
      )}

      {isLoading && (
        <div className="flex items-center gap-2 py-8">
          <Spinner />
          <span className="text-muted-foreground">Cargando usuarios...</span>
        </div>
      )}

      {data && (
        <div className="space-y-4">
          <div className="text-sm text-muted-foreground">
            {data.total} usuarios
          </div>
          <UsuarioTable
            items={data.items}
            onView={setDetailUser}
            onEdit={handleEdit}
          />
        </div>
      )}

      <UsuarioDetail user={detailUser} onClose={() => setDetailUser(null)} />
    </div>
  );
}
