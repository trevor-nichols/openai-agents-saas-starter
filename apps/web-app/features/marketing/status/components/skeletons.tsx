import { GlassPanel } from '@/components/ui/foundation';
import { Skeleton } from '@/components/ui/skeleton';
import { TableCell, TableRow } from '@/components/ui/table';

export function ServiceSkeleton() {
  return (
    <GlassPanel className="space-y-4">
      <div className="flex flex-col gap-2">
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-4 w-72" />
      </div>
      <div className="flex justify-between">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-4 w-32" />
      </div>
    </GlassPanel>
  );
}

export function MetricSkeleton() {
  return (
    <GlassPanel className="space-y-3">
      <Skeleton className="h-4 w-32" />
      <Skeleton className="h-6 w-24" />
      <Skeleton className="h-4 w-40" />
    </GlassPanel>
  );
}

export function IncidentSkeleton() {
  return (
    <TableRow>
      <TableCell>
        <Skeleton className="h-4 w-32" />
      </TableCell>
      <TableCell>
        <Skeleton className="h-4 w-40" />
      </TableCell>
      <TableCell>
        <Skeleton className="h-4 w-52" />
      </TableCell>
      <TableCell>
        <Skeleton className="h-4 w-20" />
      </TableCell>
    </TableRow>
  );
}
