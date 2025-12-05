import { InlineTag, GlassPanel } from '@/components/ui/foundation';
import type { SubscriptionBanner } from '../utils/statusFormatting';

interface VerificationBannerProps {
  banner: SubscriptionBanner | null;
}

export function VerificationBanner({ banner }: VerificationBannerProps) {
  if (!banner) return null;

  return (
    <GlassPanel className="flex flex-col gap-2 border-white/10 bg-white/10">
      <div className="flex items-center gap-3">
        <InlineTag tone={banner.tone}>{banner.title}</InlineTag>
      </div>
      <p className="text-sm text-foreground/80">{banner.description}</p>
    </GlassPanel>
  );
}
