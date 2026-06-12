import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import PermissionGuard from '@/shared/components/guards/PermissionGuard';
import { Spinner } from '@/shared/components/ui/Spinner';
import { ComisionSelector } from '../components/ComisionSelector';
import { useComisiones } from '../hooks/useComisiones';

export default function ComisionesPage() {
  const navigate = useNavigate();
  const { data: comisiones, isLoading, isError } = useComisiones();

  useEffect(() => {
    if (!isLoading && !isError && comisiones?.length === 1) {
      navigate(`/comisiones/${comisiones[0].materia_id}`, { replace: true });
    }
  }, [comisiones, isLoading, isError, navigate]);

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <PermissionGuard requiredPermissions="comisiones:read">
      <div className="mx-auto max-w-2xl py-12">
        <ComisionSelector />
      </div>
    </PermissionGuard>
  );
}
