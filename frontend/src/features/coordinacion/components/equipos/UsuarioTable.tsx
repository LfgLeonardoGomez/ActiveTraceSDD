import { useState, useId } from 'react';
import { Button } from '@/shared/components/ui/Button';
import { useUsuarios, useActualizarUsuario } from '../../hooks/useEquipos';
import { UsuarioForm } from './UsuarioForm';
import type { UsuarioDocente } from '../../types/equipos.types';

export function UsuarioTable() {
  const tableId = useId();
  const [page, setPage] = useState(0);
  const [editUsuario, setEditUsuario] = useState<UsuarioDocente | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [confirmToggle, setConfirmToggle] = useState<{ id: string; activo: boolean } | null>(null);

  const { data: usuarios, isLoading, isError, refetch } = useUsuarios();
  const actualizarMutation = useActualizarUsuario();

  const perPage = 50;

  const handleToggleEstado = async () => {
    if (!confirmToggle) return;
    try {
      await actualizarMutation.mutateAsync({
        id: confirmToggle.id,
        data: { activo: !confirmToggle.activo },
      });
    } catch {
      // handled inline
    }
    setConfirmToggle(null);
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-6 w-32 animate-pulse rounded bg-neutral-200" />
          <div className="h-9 w-36 animate-pulse rounded bg-neutral-200" />
        </div>
        <div className="overflow-x-auto rounded-lg border border-neutral-200">
          <table className="w-full text-sm">
            <thead className="bg-neutral-50">
              <tr>
                {['Nombre', 'Email', 'Rol', 'Regional', 'Estado', 'Última actualización', ''].map((h) => (
                  <th key={h} className="px-4 py-3 text-left font-medium text-neutral-500">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Array.from({ length: 5 }).map((_, i) => (
                <tr key={`${tableId}-skeleton-${i}`} className="animate-pulse border-t border-neutral-100">
                  {Array.from({ length: 7 }).map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <div className="h-4 w-20 rounded bg-neutral-200" />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-danger-200 bg-danger-50 p-6 text-center">
        <p className="text-danger-600">Error al cargar usuarios</p>
        <button
          onClick={() => refetch()}
          className="mt-2 text-sm font-medium text-primary-600 hover:underline"
        >
          Reintentar
        </button>
      </div>
    );
  }

  const paginated = (usuarios ?? []).slice(page * perPage, (page + 1) * perPage);
  const totalPages = Math.ceil((usuarios ?? []).length / perPage);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-neutral-900">Usuarios</h3>
        <Button onClick={() => { setShowCreateForm(true); setEditUsuario(null); }}>
          + Nuevo usuario
        </Button>
      </div>

      {showCreateForm && (
        <UsuarioForm
          onSuccess={() => { setShowCreateForm(false); setPage(0); }}
        />
      )}

      {editUsuario && (
        <UsuarioForm
          usuario={editUsuario}
          onSuccess={() => setEditUsuario(null)}
        />
      )}

      {confirmToggle && (
        <div className="rounded-md bg-warning-50 p-3 text-sm text-warning-700">
          ¿Confirmás {confirmToggle.activo ? 'desactivar' : 'activar'} este usuario?
          <div className="mt-2 flex gap-2">
            <Button variant="destructive" onClick={handleToggleEstado}>
              {confirmToggle.activo ? 'Desactivar' : 'Activar'}
            </Button>
            <Button variant="outline" onClick={() => setConfirmToggle(null)}>Cancelar</Button>
          </div>
        </div>
      )}

      {(!usuarios || usuarios.length === 0) && !showCreateForm ? (
        <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-6 text-center">
          <p className="text-neutral-600">No hay usuarios registrados</p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto rounded-lg border border-neutral-200">
            <table className="w-full text-sm">
              <thead className="bg-neutral-50">
                <tr>
                  {['Nombre', 'Email', 'Rol', 'Regional', 'Estado', 'Última actualización', ''].map((h) => (
                    <th key={h} className="px-4 py-3 text-left font-medium text-neutral-500">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {paginated.map((u) => (
                  <tr key={u.id} className="border-t border-neutral-100 hover:bg-neutral-50">
                    <td className="px-4 py-3 font-medium text-neutral-900">{u.nombre}</td>
                    <td className="px-4 py-3 text-neutral-700">{u.email}</td>
                    <td className="px-4 py-3 text-neutral-700">{u.rol}</td>
                    <td className="px-4 py-3 text-neutral-700">{u.regional}</td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        u.activo ? 'bg-success-100 text-success-700' : 'bg-neutral-100 text-neutral-600'
                      }`}>
                        {u.activo ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-neutral-500">
                      {/* A futuro: fecha_de_actualizacion */}
                      —
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <button
                          onClick={() => setEditUsuario(u)}
                          className="text-sm text-primary-600 hover:underline"
                        >
                          Editar
                        </button>
                        <button
                          onClick={() => setConfirmToggle({ id: u.id, activo: u.activo })}
                          className="text-sm text-danger-600 hover:underline"
                        >
                          {u.activo ? 'Desactivar' : 'Activar'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-neutral-500">
                Mostrando {page * perPage + 1}–{Math.min((page + 1) * perPage, (usuarios ?? []).length)} de {usuarios?.length}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="rounded-md border border-neutral-300 px-3 py-1 text-sm disabled:opacity-50"
                >
                  Anterior
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                  disabled={page >= totalPages - 1}
                  className="rounded-md border border-neutral-300 px-3 py-1 text-sm disabled:opacity-50"
                >
                  Siguiente
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
