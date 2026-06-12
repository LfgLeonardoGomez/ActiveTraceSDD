import { useState } from 'react';
import { Outlet, useParams } from 'react-router-dom';
import { TabNav } from '../components/TabNav';
import { ClearDataDialog } from '../components/ClearDataDialog';
import { Trash2 } from 'lucide-react';

export default function ComisionDetailPage() {
  const { materiaId } = useParams<{ materiaId: string }>();
  const [showClearDialog, setShowClearDialog] = useState(false);

  if (!materiaId) {
    return null;
  }

  return (
    <div className="space-y-6">
      <TabNav materiaId={materiaId} />
      <Outlet context={{ materiaId }} />

      <div className="flex justify-end border-t border-neutral-200 pt-4">
        <button
          onClick={() => setShowClearDialog(true)}
          className="inline-flex items-center gap-1.5 text-xs text-danger-500 hover:text-danger-700 hover:underline"
        >
          <Trash2 className="h-3.5 w-3.5" />
          Vaciar datos de esta comisión
        </button>
      </div>

      <ClearDataDialog
        materiaId={materiaId}
        materiaNombre={`comisión ${materiaId}`}
        open={showClearDialog}
        onClose={() => setShowClearDialog(false)}
      />
    </div>
  );
}
