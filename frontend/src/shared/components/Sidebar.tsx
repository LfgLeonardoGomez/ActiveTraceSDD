import { NavLink, useLocation } from 'react-router-dom';
import {
  Users,
  BookOpen,
  LayoutGrid,
  Mail,
  UsersRound,
  DollarSign,
  X,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { usePermissions } from '@/shared/hooks/usePermissions';

interface NavItem {
  label: string;
  path: string;
  icon: LucideIcon;
  permission: string;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Alumnos', path: '/alumnos', icon: Users, permission: 'alumnos:read' },
  { label: 'Materias', path: '/materias', icon: BookOpen, permission: 'materias:read' },
  { label: 'Comisiones', path: '/comisiones', icon: LayoutGrid, permission: 'comisiones:read' },
  { label: 'Comunicación', path: '/comunicacion', icon: Mail, permission: 'comunicacion:read' },
  { label: 'Equipos', path: '/equipos', icon: UsersRound, permission: 'equipos:read' },
  { label: 'Liquidaciones', path: '/liquidaciones', icon: DollarSign, permission: 'liquidaciones:read' },
];

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const location = useLocation();
  const { can } = usePermissions();

  const visibleItems = NAV_ITEMS.filter((item) => can(item.permission));

  const sidebarContent = (
    <div className="flex h-full flex-col bg-sidebar text-sidebar-foreground">
      {/* Logo */}
      <div className="flex h-16 items-center justify-between px-6">
        <span className="text-lg font-semibold">trace</span>
        <button
          onClick={onClose}
          className="rounded-md p-1 text-sidebar-muted hover:bg-sidebar-accent hover:text-sidebar-foreground lg:hidden"
          aria-label="Cerrar menú"
        >
          <X className="size-5" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {visibleItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname.startsWith(item.path);

          return (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={onClose}
              className={cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-sidebar-accent text-sidebar-foreground'
                  : 'text-sidebar-muted hover:bg-sidebar-accent hover:text-sidebar-foreground',
              )}
            >
              <Icon className="size-5" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-sidebar-border px-6 py-4">
        <p className="text-xs text-sidebar-muted">activia · trace v0.1</p>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        {sidebarContent}
      </aside>

      {/* Mobile overlay */}
      {isOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm"
            onClick={onClose}
          />
          {/* Sidebar panel */}
          <aside className="fixed inset-y-0 left-0 w-64 animate-slide-in-left">
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  );
}
