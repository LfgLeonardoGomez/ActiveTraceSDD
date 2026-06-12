import { Pencil, ToggleLeft, ToggleRight } from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import type { Materia } from '../../types/estructura.types';

interface MateriaTableProps {
  items: Materia[];
  onEdit: (item: Materia) => void;
  onToggleEstado: (item: Materia) => void;
}

export default function MateriaTable({ items, onEdit, onToggleEstado }: MateriaTableProps) {
  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead className="bg-muted">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Código</th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Nombre</th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Estado</th>
            <th className="px-4 py-3 text-right font-medium text-muted-foreground">Acciones</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {items.map((item) => (
            <tr key={item.id} className="hover:bg-muted/50">
              <td className="px-4 py-3 font-medium">{item.codigo}</td>
              <td className="px-4 py-3">{item.nombre}</td>
              <td className="px-4 py-3">
                <span
                  className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                    item.estado === 'activo' ? 'bg-emerald-100 text-emerald-700' : 'bg-neutral-100 text-neutral-700'
                  }`}
                >
                  {item.estado}
                </span>
              </td>
              <td className="px-4 py-3 text-right">
                <div className="flex justify-end gap-1">
                  <Button variant="ghost" size="icon" onClick={() => onEdit(item)} aria-label="Editar">
                    <Pencil className="size-4" />
                  </Button>
                  <Button variant="ghost" size="icon" onClick={() => onToggleEstado(item)} aria-label="Cambiar estado">
                    {item.estado === 'activo' ? (
                      <ToggleRight className="size-4 text-emerald-600" />
                    ) : (
                      <ToggleLeft className="size-4 text-neutral-500" />
                    )}
                  </Button>
                </div>
              </td>
            </tr>
          ))}
          {items.length === 0 && (
            <tr>
              <td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">
                No hay materias registradas
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
