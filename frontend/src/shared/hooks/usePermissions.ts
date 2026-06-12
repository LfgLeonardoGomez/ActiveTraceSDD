import { useAuth } from '@/shared/services/AuthContext';

interface UsePermissionsReturn {
  can: (permission: string) => boolean;
  hasPermission: (permission: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
}

export function usePermissions(): UsePermissionsReturn {
  const { user } = useAuth();

  const can = (permission: string): boolean => {
    if (!user?.roles) return false;
    return user.roles.some((role) => role.permissions.includes(permission));
  };

  const hasPermission = can;

  const hasAnyPermission = (permissions: string[]): boolean => {
    return permissions.some(can);
  };

  return { can, hasPermission, hasAnyPermission };
}
