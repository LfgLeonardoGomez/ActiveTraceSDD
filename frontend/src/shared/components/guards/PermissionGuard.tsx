import { Navigate, Outlet } from 'react-router-dom';
import { usePermissions } from '@/shared/hooks/usePermissions';

interface PermissionGuardProps {
  requiredPermissions: string | string[];
  requireAll?: boolean;
  redirectTo?: string;
  // Optional: when used as a wrapper it renders children; when used as a layout
  // route (no children) it renders the nested routes via <Outlet />.
  children?: React.ReactNode;
}

export default function PermissionGuard({
  requiredPermissions,
  requireAll = true,
  redirectTo = '/',
  children,
}: PermissionGuardProps) {
  const { can, hasAnyPermission } = usePermissions();

  const hasAccess =
    typeof requiredPermissions === 'string'
      ? can(requiredPermissions)
      : requireAll
        ? requiredPermissions.every(can)
        : hasAnyPermission(requiredPermissions);

  if (!hasAccess) {
    return <Navigate to={redirectTo} replace />;
  }

  return <>{children ?? <Outlet />}</>;
}
