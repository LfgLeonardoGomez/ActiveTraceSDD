import { Pencil, Trash2 } from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import type { SalarioPlus } from '../../types/salarios.types';

interface SalarioPlusTableProps {
  items: SalarioPlus[];
  onEdit: (item: SalarioPlus) => void;
  onDelete: (id: string) => void;
}

function formatCurrency(v: number): string {
  return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(v);
}

export default function SalarioPlusTable({ items, onEdit, onDelete }: SalarioPlusTableProps) {
  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead className="bg-muted">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Grupo</th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Rol</th>
            <th className="px-4 py-3 text-right font-medium text-muted-foreground">Monto</th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Vigencia desde</th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Vigencia hasta</th>
            <th className="px-4 py-3 text-right font-medium text-muted-foreground">Acciones</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {items.map((item) => (
            <tr key={item.id} className="hover:bg-muted/50">
              <td className="px-4 py-3 font-medium">{item.grupo}</td>
              <td className="px-4 py-3 text-muted-foreground">{item.rol}</td>
              <td className="px-4 py-3 text-right tabular-nums">{formatCurrency(item.monto)}</td>
              <td className="px-4 py-3 text-muted-foreground">{item.vigencia_desde}</td>
              <td className="px-4 py-3 text-muted-foreground">{item.vigencia_hasta}</td>
              <td className="px-4 py-3 text-right">
                <div className="flex justify-end gap-1">
                  <Button variant="ghost" size="icon" onClick={() => onEdit(item)} aria-label="Editar">
                    <Pencil className="size-4" />
                  </Button>
                  <Button variant="ghost" size="icon" onClick={() => onDelete(item.id)} aria-label="Eliminar">
                    <Trash2 className="size-4 text-danger-600" />
                  </Button>
                </div>
              </td>
            </tr>
          ))}
          {items.length === 0 && (
            <tr>
              <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                No hay salarios plus configurados
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
