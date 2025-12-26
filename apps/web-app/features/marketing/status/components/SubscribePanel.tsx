import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { GlassPanel } from '@/components/ui/foundation';
import type { CtaLink } from '@/features/marketing/types';

interface SubscribePanelProps {
  rssHref: string;
  onCtaClick: (meta: { location: string; cta: CtaLink }) => void;
}

export function SubscribePanel({ rssHref, onCtaClick }: SubscribePanelProps) {
  const rssCta: CtaLink = { label: 'RSS Feed', href: rssHref, intent: 'secondary' };
  const emailCta: CtaLink = { label: 'Email ops', href: 'mailto:status@anything.agents', intent: 'secondary' };

  return (
    <GlassPanel className="space-y-3">
      <h4 className="text-base font-semibold text-foreground">Subscribe for alerts</h4>
      <p className="text-sm text-foreground/70">Hook this status feed into your tooling via RSS or our console.</p>
      <div className="flex flex-wrap gap-2">
        <Button
          asChild
          size="sm"
          onClick={() =>
            onCtaClick({
              location: 'status-rss',
              cta: rssCta,
            })
          }
        >
          <Link href={rssHref}>RSS Feed</Link>
        </Button>
        <Button
          asChild
          size="sm"
          variant="outline"
          onClick={() =>
            onCtaClick({
              location: 'status-email-ops',
              cta: emailCta,
            })
          }
        >
          <Link href={emailCta.href}>Email ops</Link>
        </Button>
      </div>
    </GlassPanel>
  );
}
