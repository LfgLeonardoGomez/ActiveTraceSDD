import { useState, useId, useRef } from 'react';
import { Button } from '@/shared/components/ui/Button';
import { useImportarAlumnos } from '../../hooks/useColoquios';
import type { Convocatoria } from '../../types/coloquios.types';

const ALLOWED_TYPES = [
  'text/csv',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-excel',
];

interface ImportarAlumnosUploaderProps {
  convocatorias: Convocatoria[];
  defaultConvocatoriaId?: string;
}

export function ImportarAlumnosUploader({
  convocatorias,
  defaultConvocatoriaId,
}: ImportarAlumnosUploaderProps) {
  const uploaderId = useId();
  const fileRef = useRef<HTMLInputElement>(null);
  const [selectedId, setSelectedId] = useState(defaultConvocatoriaId ?? '');
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [showErrors, setShowErrors] = useState(false);

  const { mutate: importar, isPending, data: result, error } = useImportarAlumnos();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) {
      setFile(null);
      setFileError(null);
      return;
    }
    if (!ALLOWED_TYPES.includes(f.type)) {
      setFileError('Formato no soportado. Usá CSV o XLSX');
      setFile(null);
      return;
    }
    setFile(f);
    setFileError(null);
  };

  const handleSubmit = () => {
    if (!selectedId || !file) return;
    const formData = new FormData();
    formData.append('convocatoria_id', selectedId);
    formData.append('file', file);
    importar(formData);
  };

  const handleReset = () => {
    setFile(null);
    setFileError(null);
    setShowErrors(false);
    if (fileRef.current) fileRef.current.value = '';
  };

  const partialErrors = result?.errors?.length ? result.errors : [];
  const hasError = !!error;

  return (
    <div className="space-y-4 rounded-lg border border-neutral-200 bg-white p-6">
      <h3 className="text-base font-semibold text-neutral-900">Importar alumnos</h3>

      <div className="space-y-2">
        <label htmlFor={`${uploaderId}-convocatoria`} className="text-sm font-medium text-neutral-700">
          Convocatoria
        </label>
        <select
          id={`${uploaderId}-convocatoria`}
          value={selectedId}
          onChange={(e) => setSelectedId(e.target.value)}
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          <option value="">Seleccioná una convocatoria</option>
          {convocatorias.map((c) => (
            <option key={c.id} value={c.id}>
              {c.materia} — {c.titulo}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-2">
        <label htmlFor={`${uploaderId}-file`} className="text-sm font-medium text-neutral-700">
          Archivo (CSV o XLSX)
        </label>
        <input
          ref={fileRef}
          id={`${uploaderId}-file`}
          type="file"
          accept=".csv,.xlsx,.xls"
          disabled={!selectedId}
          onChange={handleFileChange}
          className="block w-full text-sm text-neutral-600 file:mr-3 file:rounded-md file:border-0 file:bg-primary-50 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-primary-700 hover:file:bg-primary-100 disabled:opacity-50"
        />
        {!selectedId && (
          <p className="text-sm text-neutral-500">Seleccioná una convocatoria primero</p>
        )}
        {fileError && <p className="text-sm text-danger-600">{fileError}</p>}
      </div>

      {isPending && (
        <div className="space-y-2">
          <div className="h-2 w-full animate-pulse rounded-full bg-primary-100">
            <div className="h-full w-1/2 rounded-full bg-primary-500" />
          </div>
          <p className="text-sm text-neutral-500">Importando...</p>
        </div>
      )}

      {result && !hasError && (
        <div className="rounded-md bg-success-50 p-3">
          <p className="text-sm font-medium text-success-700">
            {result.imported_count} alumnos importados correctamente.
            {partialErrors.length > 0 && (
              <>
                {' '}{partialErrors.length} error{partialErrors.length > 1 ? 'es' : ''}.
              </>
            )}
          </p>
          {partialErrors.length > 0 && (
            <div className="mt-2">
              <button
                onClick={() => setShowErrors(!showErrors)}
                className="text-sm font-medium text-primary-600 hover:underline"
              >
                {showErrors ? 'Ocultar errores' : 'Ver errores'}
              </button>
              {showErrors && (
                <ul className="mt-2 max-h-40 space-y-1 overflow-y-auto">
                  {partialErrors.map((e, i) => (
                    <li key={i} className="text-xs text-danger-600">
                      Fila {e.row}: {e.mensaje}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
          <button
            onClick={handleReset}
            className="mt-2 text-sm font-medium text-primary-600 hover:underline"
          >
            Importar otro archivo
          </button>
        </div>
      )}

      {hasError && (
        <div className="rounded-md bg-danger-50 p-3">
          <p className="text-sm text-danger-600">Error al importar alumnos</p>
        </div>
      )}

      <div className="flex gap-3">
        <Button
          onClick={handleSubmit}
          disabled={!selectedId || !file || isPending}
          isLoading={isPending}
        >
          Importar
        </Button>
      </div>
    </div>
  );
}
