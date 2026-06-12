import { cn } from '@/lib/utils';

interface Segment {
  key: string;
  label: string;
  count?: number;
}

interface SegmentTabsProps {
  segments: Segment[];
  active: string;
  onChange: (key: string) => void;
}

export default function SegmentTabs({ segments, active, onChange }: SegmentTabsProps) {
  return (
    <div className="flex items-center gap-1 rounded-lg border border-border bg-muted p-1">
      {segments.map((segment) => {
        const isActive = segment.key === active;
        return (
          <button
            key={segment.key}
            onClick={() => onChange(segment.key)}
            className={cn(
              'relative flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
              isActive
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:bg-background/50 hover:text-foreground',
            )}
            aria-pressed={isActive}
          >
            <span>{segment.label}</span>
            {segment.count !== undefined && (
              <span
                className={cn(
                  'inline-flex h-5 min-w-[1.25rem] items-center justify-center rounded-full px-1.5 text-xs font-medium',
                  isActive ? 'bg-primary-100 text-primary-700' : 'bg-neutral-100 text-neutral-600',
                )}
              >
                {segment.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
