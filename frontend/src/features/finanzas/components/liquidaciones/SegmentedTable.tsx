import { useState } from 'react';
import { cn } from '@/lib/utils';
import type { LiquidacionItem } from '../../types/liquidaciones.types';

interface SegmentedTableProps {
  items: LiquidacionItem[];
  segment: string;
  onRowClick?: (item: LiquidacionItem) => void;
}

export default function SegmentedTable({ items, segment, onRowClick }: SegmentedTableProps) {
  const [sortField, setSortField] = useState<keyof LiquidacionItem>('usuario_id');
  const [sortAsc, setSortAsc] = useState(true);

  const sorted = [...items].sort((a, b) => {
    const aVal = a[sortField] ?? '';
    const bVal = b[sortField] ?? '';
    if (typeof aVal === 'number' && typeof bVal === 'number') {
      return sortAsc ? aVal - bVal : bVal - aVal;
    }
    return sortAsc
      ? String(aVal).localeCompare(String(bVal))
      : String(bVal).localeCompare(String(aVal));
  });

  const total = items.reduce((sum, i) => sum + i.total, 0);

  const headers: { key: keyof LiquidacionItem; label: string }[] = [
    { key: 'usuario_id', label: 'Usuario' },
    { key: 'rol', label: 'Rol' },
    { key: 'monto_base', label: 'Salario base' },
    { key: 'monto_plus', label: 'Salario plus' },
    { key: 'total', label: 'Total' },
  ];

  function formatCurrency(v: number): string {
    return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(v);
  }

  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead className="bg-muted">
          <tr>
            {headers.map((h) => (
              <th
                key={h.key}
                className="cursor-pointer px-4 py-3 text-left font-medium text-muted-foreground hover:text-foreground"
                onClick={() => {
                  if (sortField === h.key) setSortAsc(!sortAsc);
                  else {
                    setSortField(h.key);
                    setSortAsc(true);
                  }
                }}
              >
                {h.label}
                {sortField === h.key && (sortAsc ? ' ▲' : ' ▼')}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {sorted.map((item) => (
            <tr
              key={item.usuario_id}
              className={cn(
                'transition-colors hover:bg-muted/50',
                onRowClick && 'cursor-pointer',
              )}
              onClick={() => onRowClick?.(item)}
            >
              <td className="px-4 py-3 font-mono text-xs">{item.usuario_id}</td>
              <td className="px-4 py-3 text-muted-foreground">{item.rol}</td>
              <td className="px-4 py-3 text-right tabular-nums">{formatCurrency(item.monto_base)}</td>
              <td className="px-4 py-3 text-right tabular-nums">{formatCurrency(item.monto_plus)}</td>
              <td className="px-4 py-3 text-right font-semibold tabular-nums">{formatCurrency(item.total)}</td>
            </tr>
          ))}
          {items.length === 0 && (
            <tr>
              <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                No hay datos para el segmento <strong>{segment}</strong>
              </td>
            </tr>
          )}
        </tbody>
        <tfoot className="bg-muted/50">
          <tr>
            <td colSpan={4} className="px-4 py-3 text-right font-medium">
              Subtotal {segment}
            </td>
            <td className="px-4 py-3 text-right font-bold tabular-nums">{formatCurrency(total)}</td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
