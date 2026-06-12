import { useState } from 'react';
import type { TareaComment } from '../../types/tareas.types';

interface TareaCommentThreadProps {
  comentarios: TareaComment[];
  onSendComment?: (contenido: string) => void;
  collapsed?: boolean;
}

export function TareaCommentThread({ comentarios, onSendComment, collapsed = false }: TareaCommentThreadProps) {
  const [isExpanded, setIsExpanded] = useState(!collapsed);
  const [text, setText] = useState('');

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || !onSendComment) return;
    onSendComment(trimmed);
    setText('');
  };

  const sorted = [...comentarios].sort(
    (a, b) => new Date(a.fecha).getTime() - new Date(b.fecha).getTime(),
  );

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-1 text-xs font-medium text-neutral-500 hover:text-neutral-700"
      >
        <span className={`transition-transform ${isExpanded ? 'rotate-90' : ''}`}>▶</span>
        Comentarios ({comentarios.length})
      </button>

      {isExpanded && (
        <div className="space-y-3 pl-3 border-l-2 border-neutral-200">
          {sorted.length === 0 && (
            <p className="text-xs text-neutral-400">Sin comentarios</p>
          )}

          {sorted.map((c) => (
            <div key={c.id} className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-neutral-700">{c.autor}</span>
                <span className="text-xs text-neutral-400">
                  {new Date(c.fecha).toLocaleDateString()} {new Date(c.fecha).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              <p className="text-sm text-neutral-600">{c.contenido}</p>
            </div>
          ))}

          {onSendComment && (
            <div className="flex items-start gap-2 pt-1">
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Escribí un comentario..."
                rows={2}
                className="min-h-[2.5rem] flex-1 resize-none rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm placeholder:text-neutral-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
              <button
                type="button"
                onClick={handleSend}
                disabled={!text.trim()}
                className="rounded-md bg-primary-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
              >
                Enviar
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
