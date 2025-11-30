import { GlassPanel } from '@/components/ui/foundation/GlassPanel';
import { Skeleton } from '@/components/ui/skeleton';

export default function MarketingLoading() {
  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-16 space-y-10">
      <section className="space-y-4 text-center">
        <Skeleton className="mx-auto h-10 w-64" />
        <Skeleton className="mx-auto h-4 w-80" />
      </section>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <GlassPanel key={index} className="space-y-3 p-6">
            <Skeleton className="h-5 w-2/3" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-11/12" />
            <Skeleton className="h-4 w-3/5" />
            <div className="flex gap-2 pt-2">
              <Skeleton className="h-8 w-20" />
              <Skeleton className="h-8 w-16" />
            </div>
          </GlassPanel>
        ))}
      </div>
    </div>
  );
}
