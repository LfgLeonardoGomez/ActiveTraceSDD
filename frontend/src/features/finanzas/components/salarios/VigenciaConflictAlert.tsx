import { AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface VigenciaConflictAlertProps {
  message: string;
  className?: string;
}

export default function VigenciaConflictAlert({ message, className }: VigenciaConflictAlertProps) {
  return (
    <div
      className={cn(
        'flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800',
        className,
      )}
      role="alert"
    >
      <AlertTriangle className="mt-0.5 size-4 shrink-0" />
      <span>{message}</span>
    </div>
  );
}
