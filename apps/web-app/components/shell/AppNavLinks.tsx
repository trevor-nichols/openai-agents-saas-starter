'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { Badge, type BadgeProps } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

export interface AppNavItem {
  href: string;
  label: string;
  badge?: string;
  badgeVariant?: BadgeProps['variant'];
  icon?: React.ComponentType<{ className?: string }>;
}

interface AppNavLinksProps {
  items: AppNavItem[];
  variant?: 'rail' | 'mobile';
  onNavigate?: () => void;
  className?: string;
}

function isActive(pathname: string, href: string) {
  if (!pathname) return false;
  if (pathname === href) return true;
  if (href !== '/' && pathname.startsWith(`${href}/`)) return true;
  return false;
}

export function AppNavLinks({ items, variant = 'rail', onNavigate, className }: AppNavLinksProps) {
  const pathname = usePathname() ?? '';

  return (
    <div className={cn('flex flex-col gap-1', className)}>
      {items.map((item) => {
        const active = isActive(pathname, item.href);
        const baseClasses =
          'rounded-lg px-3 py-2 text-sm font-medium transition duration-150 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/30';
        const railClasses = active
          ? 'border border-white/10 bg-white/5 text-foreground'
          : 'text-foreground/70 hover:bg-white/5 hover:text-foreground';
        const mobileClasses = active
          ? 'border border-white/10 bg-white/10 text-foreground'
          : 'text-foreground/80 hover:bg-white/5';

        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? 'page' : undefined}
            className={cn(baseClasses, variant === 'rail' ? railClasses : mobileClasses)}
            onClick={onNavigate}
          >
            <span className="flex items-center justify-between gap-2">
              <span>{item.label}</span>
              {item.badge ? (
                <Badge
                  variant={item.badgeVariant ?? 'secondary'}
                  className="rounded-full border-white/10 bg-white/10 px-2 py-0 text-[11px] font-medium text-foreground"
                >
                  {item.badge}
                </Badge>
              ) : null}
            </span>
          </Link>
        );
      })}
    </div>
  );
}
