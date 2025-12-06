import { GlassPanel } from '@/components/ui/foundation/GlassPanel';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

interface SkeletonPanelProps extends React.HTMLAttributes<HTMLDivElement> {
  lines?: number;
}

export function SkeletonPanel({ lines = 4, className, ...props }: SkeletonPanelProps) {
  return (
    <GlassPanel className={cn('space-y-3', className)} {...props}>
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton key={index} className="h-4 w-full rounded-full bg-white/10" />
      ))}
    </GlassPanel>
  );
}
