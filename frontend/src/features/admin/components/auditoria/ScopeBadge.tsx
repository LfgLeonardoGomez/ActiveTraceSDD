import { User } from 'lucide-react';

interface ScopeBadgeProps {
  isPropio: boolean;
}

export default function ScopeBadge({ isPropio }: ScopeBadgeProps) {
  if (!isPropio) return null;

  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
      <User className="size-3" />
      Vista personal
    </span>
  );
}
