import Link from 'next/link';

import { NavigationMenu, NavigationMenuItem, NavigationMenuLink, NavigationMenuList } from '@/components/ui/navigation-menu';
import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag } from '@/components/ui/foundation';
import { Badge } from '@/components/ui/badge';

import type { CtaLink } from '@/features/marketing/types';
import type { DocNavItem } from '../types';

interface DocsHeroProps {
  eyebrow: string;
  title: string;
  description: string;
  updatedAt: string;
  navItems: DocNavItem[];
  primaryCta: CtaLink;
  secondaryCta: CtaLink;
  onCtaClick: (meta: { location: string; cta: CtaLink }) => void;
}

export function DocsHero({ eyebrow, title, description, updatedAt, navItems, primaryCta, secondaryCta, onCtaClick }: DocsHeroProps) {
  const handleClick = (cta: CtaLink, location: string) => () => onCtaClick({ location, cta });

  return (
    <section className="space-y-8">
      <div className="flex items-center gap-3">
        <InlineTag tone="default">{eyebrow}</InlineTag>
        <Badge variant="outline">Last updated {updatedAt}</Badge>
      </div>
      <div className="space-y-4">
        <h1 className="text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">{title}</h1>
        <p className="text-lg text-foreground/70">{description}</p>
      </div>
      <div className="flex flex-wrap gap-4">
        <Button size="lg" onClick={handleClick(primaryCta, 'docs-hero-primary')} asChild>
          <Link href={primaryCta.href}>{primaryCta.label}</Link>
        </Button>
        <Button size="lg" variant="outline" onClick={handleClick(secondaryCta, 'docs-hero-secondary')} asChild>
          <Link href={secondaryCta.href}>{secondaryCta.label}</Link>
        </Button>
      </div>
      <GlassPanel className="space-y-3 border border-white/10">
        <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">Jump to section</p>
        <NavigationMenu>
          <NavigationMenuList>
            {navItems.map((item) => (
              <NavigationMenuItem key={item.id}>
                <NavigationMenuLink href={`#${item.id}`} className="text-sm font-semibold text-foreground hover:text-primary">
                  {item.label}
                </NavigationMenuLink>
              </NavigationMenuItem>
            ))}
          </NavigationMenuList>
        </NavigationMenu>
      </GlassPanel>
    </section>
  );
}
