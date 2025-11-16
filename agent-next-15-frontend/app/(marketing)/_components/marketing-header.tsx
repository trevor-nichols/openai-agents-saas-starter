'use client';

import { ArrowUpRight, Command as CommandIcon, Menu } from 'lucide-react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';

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
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
} from '@/components/ui/navigation-menu';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';

import {
  MARKETING_ANNOUNCEMENT,
  MARKETING_CTA_LINK,
  MARKETING_PRIMARY_LINKS,
  MARKETING_SECONDARY_LINKS,
  type MarketingNavLink,
} from './nav-links';
import { useSignupCtaTarget } from '@/features/marketing/hooks/useSignupCtaTarget';

export function MarketingHeader() {
  const pathname = usePathname();
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
    <header className="sticky top-0 z-40 border-b border-white/10 bg-background/70 backdrop-blur-glass">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-3 px-6 py-4">
        {MARKETING_ANNOUNCEMENT ? (
          <Link
            href={MARKETING_ANNOUNCEMENT.href}
            className="inline-flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-xs font-medium text-foreground/80 transition hover:border-white/20 hover:bg-white/10"
          >
            <InlineTag tone="positive">{MARKETING_ANNOUNCEMENT.tag}</InlineTag>
            <span>{MARKETING_ANNOUNCEMENT.message}</span>
            <ArrowUpRight className="h-3.5 w-3.5" aria-hidden="true" />
          </Link>
        ) : null}

        <div className="flex items-center justify-between gap-3">
          <div className="flex flex-1 items-center gap-8">
            <Link href="/" className="text-lg font-semibold tracking-tight">
              Anything Agents
            </Link>

            <NavigationMenu className="hidden flex-1 md:flex">
              <NavigationMenuList className="gap-1">
                {[...MARKETING_PRIMARY_LINKS, ...MARKETING_SECONDARY_LINKS].map((link) => (
                  <NavigationMenuItem key={link.href}>
                    <NavigationMenuLink asChild>
                      <Link
                        href={link.href}
                        className={cn(
                          'rounded-full px-4 py-2 text-sm font-medium text-foreground/70 transition-colors duration-200 hover:text-foreground',
                          pathname === link.href ? 'text-foreground' : undefined,
                        )}
                      >
                        <span className="flex items-center gap-2">
                          {link.label}
                          {link.badge ? <InlineTag tone="positive">{link.badge}</InlineTag> : null}
                        </span>
                      </Link>
                    </NavigationMenuLink>
                  </NavigationMenuItem>
                ))}
              </NavigationMenuList>
            </NavigationMenu>
          </div>

          <div className="hidden items-center gap-2 md:flex">
            <CommandMenuButton onClick={() => setIsCommandOpen(true)} />
            <ThemeToggle />
            <Button
              asChild
              variant="secondary"
              className="rounded-full border border-white/10 bg-white/5 text-sm font-semibold text-foreground"
            >
              <Link href={cta.href}>{cta.label}</Link>
            </Button>
          </div>

          <div className="flex items-center gap-2 md:hidden">
            <CommandMenuButton onClick={() => setIsCommandOpen(true)} compact />
            <ThemeToggle />
            <MobileNavSheet links={navLinks} ctaLink={ctaNavLink} />
          </div>
        </div>
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
        'rounded-full border-white/10 bg-white/5 text-sm text-foreground/80 hover:bg-white/10',
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

function MobileNavSheet({ links, ctaLink }: { links: MarketingNavLink[]; ctaLink: MarketingNavLink }) {
  const [open, setOpen] = useState(false);
  const router = useRouter();

  const handleNavigate = useCallback(
    (href: string) => {
      setOpen(false);
      router.push(href);
    },
    [router],
  );

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="outline" size="icon" className="rounded-full border-white/10 bg-white/5 text-foreground">
          <Menu className="h-4 w-4" aria-hidden="true" />
          <span className="sr-only">Open navigation</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="right" className="w-full max-w-sm border-white/10 bg-background/95 text-foreground">
        <SheetHeader>
          <SheetTitle>Navigate</SheetTitle>
        </SheetHeader>
        <div className="mt-6 flex flex-col gap-4">
          {links.map((link) => (
            <Button
              key={link.href}
              variant="ghost"
              className="flex items-center justify-between rounded-2xl border border-white/10 px-4 py-3 text-base text-foreground/80 hover:border-white/20"
              onClick={() => handleNavigate(link.href)}
            >
              <span>{link.label}</span>
              {link.badge ? <InlineTag tone="positive">{link.badge}</InlineTag> : null}
            </Button>
          ))}
          <Button className="rounded-full" onClick={() => handleNavigate(ctaLink.href)}>
            {ctaLink.label}
          </Button>
        </div>
      </SheetContent>
    </Sheet>
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
