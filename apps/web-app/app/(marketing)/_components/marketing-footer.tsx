import Link from 'next/link';
import { connection } from 'next/server';

import { Button } from '@/components/ui/button';
import { SectionHeader } from '@/components/ui/foundation/SectionHeader';

import { MarketingFooterStatus } from './marketing-footer-status';
import { MARKETING_FOOTER_COLUMNS, MARKETING_SOCIAL_LINKS } from './nav-links';

export async function MarketingFooter() {
  await connection();

  return (
    <footer className="border-t border-white/10 bg-background/80 py-12 text-sm text-foreground/80 backdrop-blur-glass">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6">
        <SectionHeader
          eyebrow="Ship faster"
          title="Enterprise-ready out of the box"
          description="Every clone inherits the authenticated shell, TanStack data layer, and production-grade agent flows."
          actions={
            <Button asChild size="sm" className="rounded-full">
              <Link href="/contact">Talk to us</Link>
            </Button>
          }
        />

        <div className="grid gap-8 sm:grid-cols-3">
          {MARKETING_FOOTER_COLUMNS.map((column) => (
            <div key={column.title} className="flex flex-col gap-3">
              <p className="text-xs font-semibold uppercase tracking-[0.3em] text-foreground/50">{column.title}</p>
              <ul className="space-y-2">
                {column.links.map((link) => (
                  <li key={link.href}>
                    <Link href={link.href} className="text-foreground/70 transition hover:text-foreground">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <MarketingFooterStatus />

        <div className="flex flex-col gap-4 border-t border-white/10 pt-6 text-xs text-foreground/60 sm:flex-row sm:items-center sm:justify-between">
          <p>&copy; {new Date().getFullYear()} Acme. All rights reserved.</p>
          <div className="flex flex-wrap items-center gap-4">
            {MARKETING_SOCIAL_LINKS.map((link) => (
              <Link
                key={link.label}
                href={link.href}
                className="transition hover:text-foreground"
                target={link.external ? '_blank' : undefined}
                rel={link.external ? 'noreferrer' : undefined}
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}
