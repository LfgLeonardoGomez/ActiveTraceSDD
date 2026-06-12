import { useState } from 'react';
import { Button } from '@/shared/components/ui/Button';
import { Download } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ExportButtonProps {
  exportUrl: string;
  disabled?: boolean;
  label?: string;
  className?: string;
}

export function ExportButton({
  exportUrl,
  disabled = false,
  label = 'Exportar CSV',
  className,
}: ExportButtonProps) {
  const [message, setMessage] = useState<string | null>(null);

  const handleExport = () => {
    window.open(exportUrl, '_blank');
    setMessage('Descarga iniciada');
    setTimeout(() => setMessage(null), 3000);
  };

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <Button
        variant="outline"
        size="sm"
        disabled={disabled}
        onClick={handleExport}
        title={disabled ? 'Sin datos para exportar' : undefined}
      >
        <Download className="mr-2 h-4 w-4" />
        {label}
      </Button>
      {message && <span className="text-xs text-success-600">{message}</span>}
    </div>
  );
}
