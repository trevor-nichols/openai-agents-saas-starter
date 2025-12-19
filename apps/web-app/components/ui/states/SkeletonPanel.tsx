import { GlassPanel } from '@/components/ui/foundation/GlassPanel';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

type SkeletonVariant = 'default' | 'card';

interface SkeletonPanelProps extends React.HTMLAttributes<HTMLDivElement> {
  lines?: number;
  variant?: SkeletonVariant;
}

export function SkeletonPanel({ lines = 4, variant = 'default', className, ...props }: SkeletonPanelProps) {
  const Container = variant === 'card' ? GlassPanel : 'div';
  const containerClass = cn(
    'space-y-3',
    variant === 'default' && 'bg-transparent p-0 shadow-none',
    className
  );

  return (
    <Container className={containerClass} {...props}>
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton key={index} className="h-4 w-full rounded-full bg-white/10" />
      ))}
    </Container>
  );
}
