import { Card, CardContent, CardHeader } from '@/shared/components/ui/Card';

export default function ChartSkeleton() {
  return (
    <Card className="animate-pulse">
      <CardHeader className="pb-2">
        <div className="h-5 w-32 rounded bg-muted" />
      </CardHeader>
      <CardContent>
        <div className="h-64 w-full rounded bg-muted" />
      </CardContent>
    </Card>
  );
}
