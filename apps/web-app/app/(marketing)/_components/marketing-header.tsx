'use client';

import { ArrowUpRight, Command as CommandIcon } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { NavBar } from '@/components/ui/nav-bar';
import { Banner, BannerAction, BannerClose, BannerTitle } from '@/components/ui/banner';
import { Button } from '@/components/ui/button';
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from '@/components/ui/command';
import { InlineTag } from '@/components/ui/foundation/InlineTag';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { cn } from '@/lib/utils';

import {
  MARKETING_ANNOUNCEMENT,
  MARKETING_CTA_LINK,
  MARKETING_PRIMARY_LINKS,
  MARKETING_SECONDARY_LINKS,
  type MarketingNavLink,
} from './nav-links';
import { useSignupCtaTarget } from '@/features/marketing/hooks/useSignupCtaTarget';

export function MarketingHeader() {
  const router = useRouter();
  const [isCommandOpen, setIsCommandOpen] = useState(false);
  const { cta } = useSignupCtaTarget();

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setIsCommandOpen((open) => !open);
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  const ctaNavLink: MarketingNavLink = {
    ...MARKETING_CTA_LINK,
    label: cta.label,
    href: cta.href,
  };

  const navLinks = [...MARKETING_PRIMARY_LINKS, ...MARKETING_SECONDARY_LINKS];

  return (
    <header className="sticky top-0 z-40 border-b border-black/10 dark:border-white/10 bg-background/70 backdrop-blur-glass">
      <div className="mx-auto w-full max-w-6xl px-6 py-4">
        {MARKETING_ANNOUNCEMENT ? (
          <Banner
            variant="muted"
            inset
            className="mb-3 flex-col items-start gap-3 rounded-2xl text-xs font-medium text-foreground/80 sm:flex-row sm:items-center sm:justify-between"
          >
            <div className="flex items-center gap-3">
              <InlineTag tone="positive">{MARKETING_ANNOUNCEMENT.tag}</InlineTag>
              <BannerTitle className="text-foreground/80 sm:text-sm">
                {MARKETING_ANNOUNCEMENT.message}
              </BannerTitle>
            </div>
            <div className="flex items-center gap-2">
              <BannerAction
                asChild
                variant="ghost"
                size="sm"
                className="border-none px-2 text-foreground/80 hover:text-foreground"
              >
                <Link href={MARKETING_ANNOUNCEMENT.href} className="inline-flex items-center gap-1">
                  View docs
                  <ArrowUpRight className="h-3.5 w-3.5" aria-hidden="true" />
                </Link>
              </BannerAction>
              <BannerClose
                aria-label="Dismiss announcement"
                className="text-foreground/50 hover:text-foreground/80"
              />
            </div>
          </Banner>
        ) : null}

        <NavBar
          className="static border-0 bg-transparent px-0 shadow-none backdrop-blur-none"
          navigationLinks={navLinks.map((link) => ({ href: link.href, label: link.label }))}
          onNavItemClick={(href) => router.push(href)}
          actions={
            <div className="flex items-center gap-2">
              <CommandMenuButton onClick={() => setIsCommandOpen(true)} compact />
              <ThemeToggle />
              <Button
                asChild
                variant="secondary"
                className="rounded-full border border-black/10 dark:border-white/10 bg-black/5 dark:bg-white/5 text-sm font-semibold text-foreground hover:bg-accent"
              >
                <Link href={cta.href}>{cta.label}</Link>
              </Button>
            </div>
          }
          logo={
            <Link href="/" className="text-lg font-semibold tracking-tight text-foreground no-underline">
              Acme
            </Link>
          }
          aria-label="Marketing navigation"
        />
      </div>

      <MarketingCommandMenu
        open={isCommandOpen}
        onOpenChange={setIsCommandOpen}
        links={[...MARKETING_PRIMARY_LINKS, ctaNavLink, ...MARKETING_SECONDARY_LINKS]}
        ctaLink={ctaNavLink}
      />
    </header>
  );
}

function CommandMenuButton({ onClick, compact }: { onClick: () => void; compact?: boolean }) {
  return (
    <Button
      variant="outline"
      size={compact ? 'icon' : 'sm'}
      className={cn(
        'rounded-full border-black/10 dark:border-white/10 bg-black/5 dark:bg-white/5 text-sm text-muted-foreground hover:bg-accent',
        compact ? 'px-0' : 'px-3',
      )}
      onClick={onClick}
    >
      <CommandIcon className="h-4 w-4" aria-hidden="true" />
      {!compact ? (
        <span className="ml-2 hidden lg:flex lg:items-center lg:gap-2">
          Quick actions
          <kbd className="rounded-md border border-white/10 bg-black/20 px-1 text-xs text-foreground/70">⌘K</kbd>
        </span>
      ) : null}
    </Button>
  );
}

interface MarketingCommandMenuProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  links: MarketingNavLink[];
  ctaLink: MarketingNavLink;
}

function MarketingCommandMenu({ open, onOpenChange, links, ctaLink }: MarketingCommandMenuProps) {
  const router = useRouter();

  const handleSelect = (href: string) => {
    onOpenChange(false);
    router.push(href);
  };

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput placeholder="Search pages and actions" />
      <CommandList>
        <CommandEmpty>No routes found.</CommandEmpty>
        <CommandGroup heading="Go to">
          {links.map((link) => (
            <CommandItem key={link.href} value={link.href} onSelect={() => handleSelect(link.href)}>
              <div className="flex flex-1 flex-col">
                <span className="text-sm font-medium">{link.label}</span>
                <span className="text-xs text-foreground/60">{link.description}</span>
              </div>
              {link.badge ? <InlineTag tone="positive">{link.badge}</InlineTag> : null}
            </CommandItem>
          ))}
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Quick actions">
          <CommandItem onSelect={() => handleSelect(ctaLink.href)}>{ctaLink.label}</CommandItem>
          <CommandItem onSelect={() => handleSelect('/contact')}>Contact sales</CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
