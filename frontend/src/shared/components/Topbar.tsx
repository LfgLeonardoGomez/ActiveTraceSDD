import { Menu, LogOut } from 'lucide-react';
import { useAuth } from '@/shared/services/AuthContext';
import { Button } from '@/shared/components/ui/Button';
import { useLogoutMutation } from '@/features/auth/hooks/useLogout';

interface TopbarProps {
  onToggleSidebar?: () => void;
}

export default function Topbar({ onToggleSidebar }: TopbarProps) {
  const { user } = useAuth();
  const logoutMutation = useLogoutMutation();

  return (
    <header className="flex h-16 items-center justify-between border-b border-border bg-background px-4 lg:px-6">
      {/* Left: mobile hamburger */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="rounded-md p-2 text-muted-foreground hover:bg-muted lg:hidden"
          aria-label="Abrir menú"
        >
          <Menu className="size-5" />
        </button>
      </div>

      {/* Right: user info + logout */}
      <div className="flex items-center gap-4">
        <span className="text-sm text-muted-foreground">
          {user?.email ?? 'Usuario'}
        </span>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => logoutMutation.mutate()}
          isLoading={logoutMutation.isPending}
        >
          <LogOut className="mr-2 size-4" />
          Salir
        </Button>
      </div>
    </header>
  );
}
