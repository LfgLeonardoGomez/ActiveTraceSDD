import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import type { AuditLogEntry } from '../../types/auditoria.types';

interface LogTableProps {
  items: AuditLogEntry[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}

export default function LogTable({ items, total, page, pageSize, onPageChange }: LogTableProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Registro de auditoría ({total})</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-hidden rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="bg-muted">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Fecha</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Usuario</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Acción</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Módulo</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Descripción</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Materia</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {items.map((item) => (
                <tr key={item.id} className="hover:bg-muted/50">
                  <td className="px-4 py-3 whitespace-nowrap text-muted-foreground">
                    {new Date(item.timestamp).toLocaleString('es-AR')}
                  </td>
                  <td className="px-4 py-3 font-medium">{item.usuario_nombre}</td>
                  <td className="px-4 py-3">
                    <span className="inline-flex rounded-md bg-primary-50 px-2 py-0.5 text-xs font-medium text-primary-700">
                      {item.accion}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{item.modulo}</td>
                  <td className="px-4 py-3">{item.descripcion}</td>
                  <td className="px-4 py-3 text-muted-foreground">{item.materia_nombre ?? '-'}</td>
                  <td className="px-4 py-3">
                    <span className="inline-flex rounded-full px-2 py-0.5 text-xs font-medium bg-neutral-100 text-neutral-700">
                      {item.estado}
                    </span>
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">
                    No hay registros de auditoría
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {totalPages > 1 && (
          <div className="mt-4 flex items-center justify-between">
            <button
              onClick={() => onPageChange(Math.max(1, page - 1))}
              disabled={page <= 1}
              className="rounded-md border border-border px-3 py-1 text-sm font-medium hover:bg-muted disabled:opacity-50"
            >
              Anterior
            </button>
            <span className="text-sm text-muted-foreground">
              Página {page} de {totalPages}
            </span>
            <button
              onClick={() => onPageChange(Math.min(totalPages, page + 1))}
              disabled={page >= totalPages}
              className="rounded-md border border-border px-3 py-1 text-sm font-medium hover:bg-muted disabled:opacity-50"
            >
              Siguiente
            </button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
