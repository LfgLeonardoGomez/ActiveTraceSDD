import type { ReactNode } from 'react';
import { ErrorBoundary, type FallbackProps } from 'react-error-boundary';
import { Button } from '@/shared/components/ui/Button';

function Fallback({ error, resetErrorBoundary }: FallbackProps) {
  return (
    <div
      role="alert"
      className="mx-auto mt-12 max-w-lg rounded-lg border border-danger-200 bg-danger-50 p-6 text-center"
    >
      <h2 className="text-lg font-semibold text-danger-600">Algo salió mal en esta vista</h2>
      <p className="mt-2 text-sm text-neutral-600">
        Ocurrió un error al renderizar esta sección. El resto de la aplicación sigue disponible.
      </p>
      {error?.message && (
        <pre className="mt-3 overflow-x-auto rounded bg-white p-3 text-left text-xs text-neutral-500">
          {error.message}
        </pre>
      )}
      <Button variant="outline" className="mt-4" onClick={resetErrorBoundary}>
        Reintentar
      </Button>
    </div>
  );
}

interface RouteErrorBoundaryProps {
  children: ReactNode;
  /** When this value changes the boundary resets — pass the route key so a
   * navigation clears a previous view's error. */
  resetKey?: string;
}

export default function RouteErrorBoundary({ children, resetKey }: RouteErrorBoundaryProps) {
  return (
    <ErrorBoundary FallbackComponent={Fallback} resetKeys={[resetKey]}>
      {children}
    </ErrorBoundary>
  );
}
