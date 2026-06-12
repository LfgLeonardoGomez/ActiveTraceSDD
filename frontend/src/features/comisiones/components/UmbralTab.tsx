import { useOutletContext } from 'react-router-dom';
import { ThresholdEditor } from './ThresholdEditor';

export function UmbralTab() {
  const { materiaId } = useOutletContext<{ materiaId: string }>();
  return <ThresholdEditor materiaId={materiaId} />;
}
