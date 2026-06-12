import { useState } from 'react';
import { Card, CardContent } from '@/shared/components/ui/Card';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Spinner } from '@/shared/components/ui/Spinner';
import { cn } from '@/lib/utils';
import {
  useCarrerasAdmin,
  useCrearCarreraAdmin,
  useActualizarCarreraAdmin,
  useCohortesAdmin,
  useCrearCohorteAdmin,
  useActualizarCohorteAdmin,
  useMateriasAdmin,
  useCrearMateriaAdmin,
  useActualizarMateriaAdmin,
} from '../hooks/useEstructuraAdmin';
import CarreraTable from '../components/estructura/CarreraTable';
import CarreraForm from '../components/estructura/CarreraForm';
import CohorteTable from '../components/estructura/CohorteTable';
import CohorteForm from '../components/estructura/CohorteForm';
import MateriaTable from '../components/estructura/MateriaTable';
import MateriaForm from '../components/estructura/MateriaForm';
import type { Carrera, Cohorte, Materia, CarreraCreate, CohorteCreate, MateriaCreate } from '../types/estructura.types';

type Tab = 'carreras' | 'cohortes' | 'materias';

export default function EstructuraPage() {
  const [tab, setTab] = useState<Tab>('carreras');
  const [nombreFilter, setNombreFilter] = useState('');
  const [estadoFilter, setEstadoFilter] = useState<'activo' | 'inactivo' | ''>('');
  const [showForm, setShowForm] = useState(false);
  const [editingCarrera, setEditingCarrera] = useState<Carrera | null>(null);
  const [editingCohorte, setEditingCohorte] = useState<Cohorte | null>(null);
  const [editingMateria, setEditingMateria] = useState<Materia | null>(null);

  const filters = {
    nombre: nombreFilter || undefined,
    estado: estadoFilter || undefined,
  };

  const { data: carreras, isLoading: carrerasLoading } = useCarrerasAdmin(filters);
  const { data: cohortes, isLoading: cohortesLoading } = useCohortesAdmin(filters);
  const { data: materias, isLoading: materiasLoading } = useMateriasAdmin(filters);

  const crearCarrera = useCrearCarreraAdmin();
  const actualizarCarrera = useActualizarCarreraAdmin();
  const crearCohorte = useCrearCohorteAdmin();
  const actualizarCohorte = useActualizarCohorteAdmin();
  const crearMateria = useCrearMateriaAdmin();
  const actualizarMateria = useActualizarMateriaAdmin();

  const isMutating =
    crearCarrera.isPending ||
    actualizarCarrera.isPending ||
    crearCohorte.isPending ||
    actualizarCohorte.isPending ||
    crearMateria.isPending ||
    actualizarMateria.isPending;

  const handleCreateCarrera = (data: CarreraCreate) => {
    crearCarrera.mutate(data, { onSuccess: () => setShowForm(false) });
  };

  const handleUpdateCarrera = (data: CarreraCreate) => {
    if (!editingCarrera) return;
    actualizarCarrera.mutate({ id: editingCarrera.id, data }, { onSuccess: () => { setShowForm(false); setEditingCarrera(null); } });
  };

  const handleToggleCarrera = (item: Carrera) => {
    actualizarCarrera.mutate({
      id: item.id,
      data: { estado: item.estado === 'activo' ? 'inactivo' : 'activo' },
    });
  };

  const handleCreateCohorte = (data: CohorteCreate) => {
    crearCohorte.mutate(data, { onSuccess: () => setShowForm(false) });
  };

  const handleUpdateCohorte = (data: CohorteCreate) => {
    if (!editingCohorte) return;
    actualizarCohorte.mutate({ id: editingCohorte.id, data }, { onSuccess: () => { setShowForm(false); setEditingCohorte(null); } });
  };

  const handleToggleCohorte = (item: Cohorte) => {
    actualizarCohorte.mutate({
      id: item.id,
      data: { estado: item.estado === 'activo' ? 'inactivo' : 'activo' },
    });
  };

  const handleCreateMateria = (data: MateriaCreate) => {
    crearMateria.mutate(data, { onSuccess: () => setShowForm(false) });
  };

  const handleUpdateMateria = (data: MateriaCreate) => {
    if (!editingMateria) return;
    actualizarMateria.mutate({ id: editingMateria.id, data }, { onSuccess: () => { setShowForm(false); setEditingMateria(null); } });
  };

  const handleToggleMateria = (item: Materia) => {
    actualizarMateria.mutate({
      id: item.id,
      data: { estado: item.estado === 'activo' ? 'inactivo' : 'activo' },
    });
  };

  const isLoading = tab === 'carreras' ? carrerasLoading : tab === 'cohortes' ? cohortesLoading : materiasLoading;

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold tracking-tight">Estructura académica</h1>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-1 rounded-lg border border-border bg-muted p-1">
          {(['carreras', 'cohortes', 'materias'] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => {
                setTab(t);
                setShowForm(false);
                setEditingCarrera(null);
                setEditingCohorte(null);
                setEditingMateria(null);
              }}
              className={cn(
                'rounded-md px-3 py-1.5 text-sm font-medium capitalize transition-colors',
                tab === t ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:bg-background/50',
              )}
            >
              {t}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <Input
            placeholder="Buscar por nombre..."
            value={nombreFilter}
            onChange={(e) => setNombreFilter(e.target.value)}
            className="w-56"
          />
          <select
            value={estadoFilter}
            onChange={(e) => setEstadoFilter(e.target.value as 'activo' | 'inactivo' | '')}
            className="h-10 w-32 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
          >
            <option value="">Todos</option>
            <option value="activo">Activo</option>
            <option value="inactivo">Inactivo</option>
          </select>
          <Button
            onClick={() => {
              setShowForm(true);
              setEditingCarrera(null);
              setEditingCohorte(null);
              setEditingMateria(null);
            }}
          >
            Nuevo
          </Button>
        </div>
      </div>

      {showForm && tab === 'carreras' && (
        <CarreraForm
          item={editingCarrera}
          onSubmit={editingCarrera ? handleUpdateCarrera : handleCreateCarrera}
          onCancel={() => { setShowForm(false); setEditingCarrera(null); }}
          isLoading={isMutating}
        />
      )}

      {showForm && tab === 'cohortes' && (
        <CohorteForm
          item={editingCohorte}
          carreras={carreras?.map((c) => ({ id: c.id, nombre: c.nombre })) ?? []}
          onSubmit={editingCohorte ? handleUpdateCohorte : handleCreateCohorte}
          onCancel={() => { setShowForm(false); setEditingCohorte(null); }}
          isLoading={isMutating}
        />
      )}

      {showForm && tab === 'materias' && (
        <MateriaForm
          item={editingMateria}
          onSubmit={editingMateria ? handleUpdateMateria : handleCreateMateria}
          onCancel={() => { setShowForm(false); setEditingMateria(null); }}
          isLoading={isMutating}
        />
      )}

      {isLoading && (
        <div className="flex items-center gap-2 py-8">
          <Spinner />
          <span className="text-muted-foreground">Cargando...</span>
        </div>
      )}

      {tab === 'carreras' && carreras && (
        <CarreraTable
          items={carreras}
          onEdit={(item) => { setEditingCarrera(item); setEditingCohorte(null); setEditingMateria(null); setShowForm(true); }}
          onToggleEstado={handleToggleCarrera}
        />
      )}

      {tab === 'cohortes' && cohortes && (
        <CohorteTable
          items={cohortes}
          onEdit={(item) => { setEditingCohorte(item); setEditingCarrera(null); setEditingMateria(null); setShowForm(true); }}
          onToggleEstado={handleToggleCohorte}
        />
      )}

      {tab === 'materias' && materias && (
        <MateriaTable
          items={materias}
          onEdit={(item) => { setEditingMateria(item); setEditingCarrera(null); setEditingCohorte(null); setShowForm(true); }}
          onToggleEstado={handleToggleMateria}
        />
      )}
    </div>
  );
}
