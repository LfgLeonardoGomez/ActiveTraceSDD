import { Eye } from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import type { Usuario } from '../../types/usuarios.types';

interface UsuarioTableProps {
  items: Usuario[];
  onView: (item: Usuario) => void;
  onEdit: (item: Usuario) => void;
}

function statusBadge(estado: Usuario['estado']) {
  const styles: Record<Usuario['estado'], string> = {
    activo: 'bg-emerald-100 text-emerald-700',
    inactivo: 'bg-neutral-100 text-neutral-700',
    pendiente: 'bg-amber-100 text-amber-700',
  };
  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${styles[estado]}`}>{estado}</span>
  );
}

export default function UsuarioTable({ items, onView, onEdit }: UsuarioTableProps) {
  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead className="bg-muted">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Nombre</th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Email</th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Roles</th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Estado</th>
            <th className="px-4 py-3 text-right font-medium text-muted-foreground">Acciones</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {items.map((item) => (
            <tr key={item.id} className="hover:bg-muted/50">
              <td className="px-4 py-3 font-medium">{item.nombre}</td>
              <td className="px-4 py-3 text-muted-foreground">{item.email}</td>
              <td className="px-4 py-3">
                <div className="flex flex-wrap gap-1">
                  {item.roles.map((rol) => (
                    <span key={rol} className="inline-flex rounded-md bg-primary-50 px-2 py-0.5 text-xs font-medium text-primary-700">
                      {rol}
                    </span>
                  ))}
                </div>
              </td>
              <td className="px-4 py-3">{statusBadge(item.estado)}</td>
              <td className="px-4 py-3 text-right">
                <div className="flex justify-end gap-1">
                  <Button variant="ghost" size="icon" onClick={() => onView(item)} aria-label="Ver detalle">
                    <Eye className="size-4" />
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => onEdit(item)}>
                    Editar
                  </Button>
                </div>
              </td>
            </tr>
          ))}
          {items.length === 0 && (
            <tr>
              <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                No hay usuarios registrados
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
