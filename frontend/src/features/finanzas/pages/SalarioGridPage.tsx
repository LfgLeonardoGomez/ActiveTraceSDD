import { useState } from 'react';
import { Card, CardContent } from '@/shared/components/ui/Card';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Spinner } from '@/shared/components/ui/Spinner';
import { cn } from '@/lib/utils';
import {
  useSalarioBase,
  useSalarioPlus,
  useCrearSalarioBase,
  useActualizarSalarioBase,
  useEliminarSalarioBase,
  useCrearSalarioPlus,
  useActualizarSalarioPlus,
  useEliminarSalarioPlus,
} from '../hooks/useSalarios';
import SalarioBaseTable from '../components/salarios/SalarioBaseTable';
import SalarioBaseForm from '../components/salarios/SalarioBaseForm';
import SalarioPlusTable from '../components/salarios/SalarioPlusTable';
import SalarioPlusForm from '../components/salarios/SalarioPlusForm';
import VigenciaConflictAlert from '../components/salarios/VigenciaConflictAlert';
import type { SalarioBase, SalarioPlus, SalarioBaseCreate, SalarioPlusCreate } from '../types/salarios.types';

type Tab = 'base' | 'plus';

export default function SalarioGridPage() {
  const [tab, setTab] = useState<Tab>('base');
  const [rolFilter, setRolFilter] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingBase, setEditingBase] = useState<SalarioBase | null>(null);
  const [editingPlus, setEditingPlus] = useState<SalarioPlus | null>(null);
  const [conflict, setConflict] = useState<string | null>(null);

  const { data: baseItems, isLoading: baseLoading } = useSalarioBase({ rol: rolFilter || undefined });
  const { data: plusItems, isLoading: plusLoading } = useSalarioPlus({ rol: rolFilter || undefined });

  const crearBase = useCrearSalarioBase();
  const actualizarBase = useActualizarSalarioBase();
  const eliminarBase = useEliminarSalarioBase();
  const crearPlus = useCrearSalarioPlus();
  const actualizarPlus = useActualizarSalarioPlus();
  const eliminarPlus = useEliminarSalarioPlus();

  const handleCreateBase = (data: SalarioBaseCreate) => {
    crearBase.mutate(data, {
      onSuccess: () => {
        setShowForm(false);
        setConflict(null);
      },
      onError: (err) => {
        setConflict(err instanceof Error ? err.message : 'Conflicto de vigencia detectado');
      },
    });
  };

  const handleUpdateBase = (data: SalarioBaseCreate) => {
    if (!editingBase) return;
    actualizarBase.mutate(
      { id: editingBase.id, data },
      {
        onSuccess: () => {
          setShowForm(false);
          setEditingBase(null);
          setConflict(null);
        },
        onError: (err) => {
          setConflict(err instanceof Error ? err.message : 'Conflicto de vigencia detectado');
        },
      },
    );
  };

  const handleDeleteBase = (id: string) => {
    if (confirm('¿Eliminar este salario base?')) {
      eliminarBase.mutate(id);
    }
  };

  const handleCreatePlus = (data: SalarioPlusCreate) => {
    crearPlus.mutate(data, {
      onSuccess: () => {
        setShowForm(false);
        setConflict(null);
      },
      onError: (err) => {
        setConflict(err instanceof Error ? err.message : 'Conflicto de vigencia detectado');
      },
    });
  };

  const handleUpdatePlus = (data: SalarioPlusCreate) => {
    if (!editingPlus) return;
    actualizarPlus.mutate(
      { id: editingPlus.id, data },
      {
        onSuccess: () => {
          setShowForm(false);
          setEditingPlus(null);
          setConflict(null);
        },
        onError: (err) => {
          setConflict(err instanceof Error ? err.message : 'Conflicto de vigencia detectado');
        },
      },
    );
  };

  const handleDeletePlus = (id: string) => {
    if (confirm('¿Eliminar este salario plus?')) {
      eliminarPlus.mutate(id);
    }
  };

  const isLoading = tab === 'base' ? baseLoading : plusLoading;
  const isMutating =
    crearBase.isPending ||
    actualizarBase.isPending ||
    eliminarBase.isPending ||
    crearPlus.isPending ||
    actualizarPlus.isPending ||
    eliminarPlus.isPending;

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold tracking-tight">Grilla salarial</h1>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-1 rounded-lg border border-border bg-muted p-1">
          <button
            onClick={() => {
              setTab('base');
              setShowForm(false);
              setEditingBase(null);
              setEditingPlus(null);
              setConflict(null);
            }}
            className={cn(
              'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
              tab === 'base' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:bg-background/50',
            )}
          >
            Salario base
          </button>
          <button
            onClick={() => {
              setTab('plus');
              setShowForm(false);
              setEditingBase(null);
              setEditingPlus(null);
              setConflict(null);
            }}
            className={cn(
              'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
              tab === 'plus' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:bg-background/50',
            )}
          >
            Salario plus
          </button>
        </div>

        <div className="flex items-center gap-2">
          <Input
            placeholder="Filtrar por rol..."
            value={rolFilter}
            onChange={(e) => setRolFilter(e.target.value)}
            className="w-56"
          />
          <Button
            onClick={() => {
              setShowForm(true);
              setEditingBase(null);
              setEditingPlus(null);
            }}
          >
            Nuevo
          </Button>
        </div>
      </div>

      {conflict && <VigenciaConflictAlert message={conflict} className="mb-4" />}

      {showForm && tab === 'base' && (
        <SalarioBaseForm
          item={editingBase}
          onSubmit={editingBase ? handleUpdateBase : handleCreateBase}
          onCancel={() => {
            setShowForm(false);
            setEditingBase(null);
            setConflict(null);
          }}
          isLoading={isMutating}
        />
      )}

      {showForm && tab === 'plus' && (
        <SalarioPlusForm
          item={editingPlus}
          onSubmit={editingPlus ? handleUpdatePlus : handleCreatePlus}
          onCancel={() => {
            setShowForm(false);
            setEditingPlus(null);
            setConflict(null);
          }}
          isLoading={isMutating}
        />
      )}

      {isLoading && (
        <div className="flex items-center gap-2 py-8">
          <Spinner />
          <span className="text-muted-foreground">Cargando...</span>
        </div>
      )}

      {tab === 'base' && baseItems && (
        <SalarioBaseTable
          items={baseItems}
          onEdit={(item) => {
            setEditingBase(item);
            setEditingPlus(null);
            setShowForm(true);
          }}
          onDelete={handleDeleteBase}
        />
      )}

      {tab === 'plus' && plusItems && (
        <SalarioPlusTable
          items={plusItems}
          onEdit={(item) => {
            setEditingPlus(item);
            setEditingBase(null);
            setShowForm(true);
          }}
          onDelete={handleDeletePlus}
        />
      )}
    </div>
  );
}
