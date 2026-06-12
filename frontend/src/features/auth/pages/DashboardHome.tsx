import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/shared/services/AuthContext';
import { usePermissions } from '@/shared/hooks/usePermissions';
import { Button } from '@/shared/components/ui/Button';

const ROUTE_PRIORITY = [
  { path: '/alumnos', permission: 'alumnos:read' },
  { path: '/materias', permission: 'materias:read' },
  { path: '/comisiones', permission: 'comisiones:read' },
  { path: '/comunicacion', permission: 'comunicacion:read' },
  { path: '/equipos', permission: 'equipos:read' },
  { path: '/liquidaciones', permission: 'liquidaciones:read' },
];

export default function DashboardHome() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { can } = usePermissions();

  useEffect(() => {
    for (const route of ROUTE_PRIORITY) {
      if (can(route.permission)) {
        navigate(route.path, { replace: true });
        return;
      }
    }
  }, [can, navigate]);

  return (
    <div className="flex flex-col items-center justify-center gap-4 py-20">
      <h2 className="text-xl font-semibold text-neutral-900">
        Bienvenido, {user?.nombre ?? 'usuario'}
      </h2>
      <p className="text-muted-foreground">
        No tenés acceso a ningún módulo. Contactá al administrador.
      </p>
      <Button variant="outline" onClick={() => logout()}>
        Cerrar sesión
      </Button>
    </div>
  );
}
