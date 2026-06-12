import { TrendingUp, TrendingDown } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { cn } from '@/lib/utils';

interface KPICardProps {
  title: string;
  value: number;
  delta?: number;
  format?: 'currency' | 'number';
  className?: string;
}

function formatValue(value: number, format?: 'currency' | 'number'): string {
  if (format === 'currency') {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
    }).format(value);
  }
  return new Intl.NumberFormat('es-AR').format(value);
}

export default function KPICard({ title, value, delta, format = 'number', className }: KPICardProps) {
  return (
    <Card className={cn('min-w-[200px]', className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold tracking-tight">{formatValue(value, format)}</div>
        {delta !== undefined && (
          <div className={cn('mt-1 flex items-center text-xs font-medium', delta >= 0 ? 'text-emerald-600' : 'text-red-600')}>
            {delta >= 0 ? <TrendingUp className="mr-1 size-3" /> : <TrendingDown className="mr-1 size-3" />}
            {delta >= 0 ? '+' : ''}
            {formatValue(delta, format)}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
