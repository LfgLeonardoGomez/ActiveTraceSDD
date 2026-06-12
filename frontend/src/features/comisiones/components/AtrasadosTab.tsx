import { useState } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import { AtrasadosTable } from './AtrasadosTable';
import { ComunicacionPreview } from './ComunicacionPreview';

export function AtrasadosTab() {
  const { materiaId } = useOutletContext<{ materiaId: string }>();
  const navigate = useNavigate();
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [showPreview, setShowPreview] = useState(false);

  const handleCommunicate = () => {
    if (selectedIds.length === 0) return;
    setShowPreview(true);
  };

  const handleSendSuccess = (loteId: string) => {
    setShowPreview(false);
    setSelectedIds([]);
    navigate(`/comisiones/${materiaId}/comunicaciones`, { state: { loteId } });
  };

  return (
    <div className="space-y-4">
      <AtrasadosTable
        materiaId={materiaId}
        selectedIds={selectedIds}
        onSelectionChange={setSelectedIds}
        onCommunicate={handleCommunicate}
      />

      {showPreview && (
        <ComunicacionPreview
          materiaId={materiaId}
          alumnoIds={selectedIds}
          onSuccess={handleSendSuccess}
          onClose={() => setShowPreview(false)}
        />
      )}
    </div>
  );
}
