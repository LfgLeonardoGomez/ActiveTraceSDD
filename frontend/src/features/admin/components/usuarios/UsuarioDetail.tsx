import { X, CreditCard, Building2, MapPin } from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import type { Usuario } from '../../types/usuarios.types';

interface UsuarioDetailProps {
  user: Usuario | null;
  onClose: () => void;
}

export default function UsuarioDetail({ user, onClose }: UsuarioDetailProps) {
  if (!user) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-end bg-black/30 p-4 backdrop-blur-sm sm:items-center sm:justify-center">
      <Card className="w-full max-w-md animate-in slide-in-from-bottom-4">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-lg">{user.nombre}</CardTitle>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Cerrar">
            <X className="size-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-sm text-muted-foreground">{user.email}</div>

          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-md bg-muted p-3">
              <div className="text-xs text-muted-foreground">DNI</div>
              <div className="font-medium">{user.dni ?? '-'}</div>
            </div>
            <div className="rounded-md bg-muted p-3">
              <div className="text-xs text-muted-foreground">CUIL</div>
              <div className="font-medium">{user.cuil ?? '-'}</div>
            </div>
            <div className="rounded-md bg-muted p-3">
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <CreditCard className="size-3" />
                CBU
              </div>
              <div className="font-medium">{user.cbu ?? '-'}</div>
            </div>
            <div className="rounded-md bg-muted p-3">
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Building2 className="size-3" />
                Banco
              </div>
              <div className="font-medium">{user.banco ?? '-'}</div>
            </div>
            <div className="rounded-md bg-muted p-3">
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <MapPin className="size-3" />
                Regional
              </div>
              <div className="font-medium">{user.regional ?? '-'}</div>
            </div>
            <div className="rounded-md bg-muted p-3">
              <div className="text-xs text-muted-foreground">Estado</div>
              <div className="font-medium capitalize">{user.estado}</div>
            </div>
          </div>

          <div className="flex flex-wrap gap-1">
            {user.roles.map((rol) => (
              <span key={rol} className="inline-flex rounded-md bg-primary-50 px-2 py-0.5 text-xs font-medium text-primary-700">
                {rol}
              </span>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
