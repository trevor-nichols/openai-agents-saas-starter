import { GlassPanel } from '@/components/ui/foundation';
import { Separator } from '@/components/ui/separator';
import { DEFAULT_STATUS_DESCRIPTION } from '../utils/statusFormatting';

interface OverviewPanelProps {
  description?: string | null;
}

export function OverviewPanel({ description }: OverviewPanelProps) {
  return (
    <GlassPanel className="space-y-3">
      <p className="text-base text-foreground/80">{description ?? DEFAULT_STATUS_DESCRIPTION}</p>
      <Separator className="border-white/5" />
      <div className="flex flex-wrap gap-3 text-sm text-foreground/60">
        <span>• Backend: `/health` & `/health/ready`</span>
        <span>• Frontend: App Router diagnostics</span>
        <span>• Workers: Stripe dispatcher, retry worker</span>
      </div>
    </GlassPanel>
  );
}
