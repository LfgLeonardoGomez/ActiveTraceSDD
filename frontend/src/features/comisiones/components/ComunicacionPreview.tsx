import { useState } from 'react';
import { Button } from '@/shared/components/ui/Button';
import { Spinner } from '@/shared/components/ui/Spinner';
import { useComunicacionPreview, useComunicacionEnviar } from '../hooks/useComunicaciones';
import type { ComunicacionPreview as ComunicacionPreviewType } from '../types/comisiones.types';
import { X } from 'lucide-react';

interface ComunicacionPreviewProps {
  materiaId: string;
  alumnoIds: string[];
  onSuccess: (loteId: string) => void;
  onClose: () => void;
}

export function ComunicacionPreview({
  materiaId,
  alumnoIds,
  onSuccess,
  onClose,
}: ComunicacionPreviewProps) {
  const previewMutation = useComunicacionPreview();
  const sendMutation = useComunicacionEnviar();
  const [preview, setPreview] = useState<ComunicacionPreviewType | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [error, setError] = useState<string | null>(null);

  const generatePreview = async () => {
    setError(null);
    try {
      const result = await previewMutation.mutateAsync({ materia_id: materiaId, alumno_ids: alumnoIds });
      setPreview(result);
      setSubject(result.asunto);
      setBody(result.cuerpo);
    } catch {
      setError('Error al generar la previsualización');
    }
  };

  if (!preview && !previewMutation.isPending && !error) {
    generatePreview();
  }

  const handleSend = async () => {
    setError(null);
    try {
      const result = await sendMutation.mutateAsync({
        materia_id: materiaId,
        alumno_ids: alumnoIds,
        asunto: subject,
        cuerpo: body,
      });
      onSuccess(result.lote_id);
    } catch {
      setError('Error al enviar la comunicación. Intentá de nuevo.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div
        className="w-full max-w-lg rounded-lg bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-neutral-200 px-6 py-4">
          <h2 className="text-lg font-semibold text-neutral-900">Previsualización de comunicación</h2>
          <button onClick={onClose} className="text-neutral-400 hover:text-neutral-600">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4 px-6 py-4">
          <p className="text-sm text-neutral-600">
            Se enviará a {alumnoIds.length} destinatario{alumnoIds.length !== 1 ? 's' : ''}
          </p>

          {previewMutation.isPending && (
            <div className="flex items-center justify-center gap-2 py-8">
              <Spinner size="sm" />
              <span className="text-sm text-neutral-600">Generando previsualización...</span>
            </div>
          )}

          {error && (
            <div className="rounded-md bg-danger-50 p-3 text-sm text-danger-600">
              {error}
            </div>
          )}

          {preview && !previewMutation.isPending && (
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-neutral-700">Asunto</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-1.5 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                  />
                ) : (
                  <p className="mt-1 rounded-md bg-neutral-50 px-3 py-1.5 text-sm text-neutral-900">
                    {subject}
                  </p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-neutral-700">Cuerpo</label>
                {isEditing ? (
                  <textarea
                    value={body}
                    onChange={(e) => setBody(e.target.value)}
                    rows={6}
                    className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-1.5 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                  />
                ) : (
                  <div className="mt-1 whitespace-pre-wrap rounded-md bg-neutral-50 px-3 py-1.5 text-sm text-neutral-900">
                    {body}
                  </div>
                )}
              </div>
            </div>
          )}

          {sendMutation.isPending && (
            <div className="flex items-center justify-center gap-2 text-sm text-neutral-600">
              <Spinner size="sm" />
              <span>Enviando comunicación...</span>
            </div>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 border-t border-neutral-200 px-6 py-4">
          <Button variant="outline" onClick={onClose} disabled={sendMutation.isPending}>
            Cancelar
          </Button>
          {preview && !isEditing && (
            <Button variant="ghost" onClick={() => setIsEditing(true)} disabled={sendMutation.isPending}>
              Editar
            </Button>
          )}
          {isEditing && (
            <Button variant="ghost" onClick={() => setIsEditing(false)} disabled={sendMutation.isPending}>
              Vista previa
            </Button>
          )}
          <Button
            onClick={handleSend}
            isLoading={sendMutation.isPending}
            disabled={previewMutation.isPending || !!error}
          >
            Enviar a {alumnoIds.length} destinatario{alumnoIds.length !== 1 ? 's' : ''}
          </Button>
        </div>
      </div>
    </div>
  );
}
