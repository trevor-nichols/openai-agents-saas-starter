import { Skeleton } from '@/components/ui/skeleton';
import { SkeletonPanel } from '@/components/ui/states/SkeletonPanel';

export default function AppShellLoading() {
  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center gap-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-8 w-24" />
        <Skeleton className="h-8 w-24" />
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <SkeletonPanel key={index} lines={5} className="p-5" />
        ))}
      </div>

      <SkeletonPanel lines={10} className="min-h-[320px]" />
    </div>
  );
}
