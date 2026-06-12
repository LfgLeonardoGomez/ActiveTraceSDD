import { useState, useId } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Spinner } from '@/shared/components/ui/Spinner';
import { useProgramas, useSubirPrograma, useEliminarPrograma } from '../../hooks/useEstructura';
import { descargarPrograma } from '../../services/estructura.api';

const ALLOWED_TYPES = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];

const schema = z.object({
  materia: z.string().min(1, 'Materia requerida'),
  titulo: z.string().min(1, 'Título requerido'),
  file: z
    .instanceof(FileList)
    .refine((files) => files.length > 0, 'Archivo requerido')
    .refine(
      (files) => files.length > 0 && ALLOWED_TYPES.includes(files[0].type),
      'Formato permitido: PDF, DOC, DOCX',
    ),
});

type FormValues = z.infer<typeof schema>;

export function ProgramaUploader() {
  const uploadId = useId();
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const { data: programas, isLoading, isError, refetch } = useProgramas();
  const subirMutation = useSubirPrograma();
  const eliminarMutation = useEliminarPrograma();
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (values: FormValues) => {
    setMessage(null);
    try {
      const formData = new FormData();
      formData.append('file', values.file[0]);
      formData.append('materia', values.materia);
      formData.append('titulo', values.titulo);
      await subirMutation.mutateAsync(formData);
      setMessage({ type: 'success', text: 'Programa subido correctamente' });
      reset();
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 409) {
        setMessage({ type: 'error', text: 'Ya existe un programa con ese título para la materia seleccionada' });
      } else {
        setMessage({ type: 'error', text: 'Error al subir el programa' });
      }
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await eliminarMutation.mutateAsync(id);
      setDeleteConfirm(null);
    } catch {
      setMessage({ type: 'error', text: 'Error al eliminar el programa' });
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Subir Programa</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <Input
              label="Materia"
              placeholder="Nombre de la materia"
              {...register('materia')}
              error={errors.materia?.message}
            />
            <Input
              label="Título del programa"
              placeholder="Ej: Programa 2025"
              {...register('titulo')}
              error={errors.titulo?.message}
            />
            <div className="space-y-2">
              <label htmlFor={`${uploadId}-file`} className="text-sm font-medium text-neutral-700">
                Archivo (PDF, DOC, DOCX)
              </label>
              <input
                id={`${uploadId}-file`}
                type="file"
                accept=".pdf,.doc,.docx"
                className="block w-full text-sm text-neutral-500 file:mr-4 file:rounded-md file:border-0 file:bg-primary-50 file:px-4 file:py-2 file:text-sm file:font-medium file:text-primary-700 hover:file:bg-primary-100"
                {...register('file')}
              />
              {errors.file && <p className="text-sm text-danger-600">{errors.file.message}</p>}
            </div>

            {message && (
              <div
                className={`rounded-md p-3 text-sm ${
                  message.type === 'success' ? 'bg-success-50 text-success-600' : 'bg-danger-50 text-danger-600'
                }`}
              >
                {message.text}
              </div>
            )}

            <Button type="submit" isLoading={subirMutation.isPending} disabled={subirMutation.isPending}>
              {subirMutation.isPending ? 'Subiendo...' : 'Subir programa'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Programas</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Spinner size="lg" />
            </div>
          ) : isError ? (
            <div className="rounded-lg border border-danger-200 bg-danger-50 p-6 text-center">
              <p className="text-danger-600">Error al cargar los programas</p>
              <button
                onClick={() => refetch()}
                className="mt-2 text-sm font-medium text-primary-600 hover:underline"
              >
                Reintentar
              </button>
            </div>
          ) : !programas || programas.length === 0 ? (
            <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-6 text-center">
              <p className="text-neutral-600">No hay programas cargados</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-neutral-200 text-left">
                    <th className="pb-3 pr-4 font-medium text-neutral-600">Materia</th>
                    <th className="pb-3 pr-4 font-medium text-neutral-600">Título</th>
                    <th className="pb-3 pr-4 font-medium text-neutral-600">Archivo</th>
                    <th className="pb-3 pr-4 font-medium text-neutral-600">Subido</th>
                    <th className="pb-3 font-medium text-neutral-600">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {programas.map((p) => (
                    <tr key={p.id} className="border-b border-neutral-100">
                      <td className="py-3 pr-4 text-neutral-900">{p.materia}</td>
                      <td className="py-3 pr-4 text-neutral-900">{p.titulo}</td>
                      <td className="py-3 pr-4 text-neutral-600">{p.filename}</td>
                      <td className="py-3 pr-4 text-neutral-600">
                        {new Date(p.fecha_subida).toLocaleDateString()}
                      </td>
                      <td className="py-3">
                        <div className="flex gap-2">
                          <a
                            href={descargarPrograma(p.id)}
                            download
                            className="text-sm font-medium text-primary-600 hover:underline"
                          >
                            Descargar
                          </a>
                          {deleteConfirm === p.id ? (
                            <div className="flex gap-1">
                              <button
                                onClick={() => handleDelete(p.id)}
                                className="text-sm font-medium text-danger-600 hover:underline"
                              >
                                Confirmar
                              </button>
                              <button
                                onClick={() => setDeleteConfirm(null)}
                                className="text-sm font-medium text-neutral-500 hover:underline"
                              >
                                Cancelar
                              </button>
                            </div>
                          ) : (
                            <button
                              onClick={() => setDeleteConfirm(p.id)}
                              className="text-sm font-medium text-danger-600 hover:underline"
                            >
                              Eliminar
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
