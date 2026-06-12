import { cn } from '@/lib/utils';

interface SpinnerProps {
  size?: 'sm' | 'default' | 'lg';
  className?: string;
}

export function Spinner({ size = 'default', className }: SpinnerProps) {
  return (
    <div
      className={cn(
        'animate-spin rounded-full border-2 border-current border-t-transparent text-primary-600',
        {
          'h-4 w-4': size === 'sm',
          'h-6 w-6': size === 'default',
          'h-8 w-8 border-[3px]': size === 'lg',
        },
        className,
      )}
      role="status"
      aria-label="Cargando"
    />
  );
}
