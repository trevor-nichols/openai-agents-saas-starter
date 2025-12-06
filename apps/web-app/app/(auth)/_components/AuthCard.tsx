import * as React from 'react';

import { GlassPanel } from '@/components/ui/foundation/GlassPanel';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { cn } from '@/lib/utils';

interface AuthCardProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  description?: string;
  badge?: string;
  footer?: React.ReactNode;
  children: React.ReactNode;
  showThemeToggle?: boolean;
}

export function AuthCard({
  title,
  description,
  badge,
  footer,
  children,
  className,
  showThemeToggle = true,
  ...props
}: AuthCardProps) {
  return (
    <GlassPanel
      className={cn('w-full max-w-md border-white/15 bg-white/5 p-10 text-left shadow-2xl backdrop-blur-2xl', className)}
      {...props}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          {badge ? (
            <span className="inline-flex items-center rounded-full border border-white/15 px-3 py-1 text-xs uppercase tracking-wide text-foreground/80">
              {badge}
            </span>
          ) : null}
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">{title}</h1>
            {description ? <p className="mt-1 text-sm text-foreground/70">{description}</p> : null}
          </div>
        </div>
        {showThemeToggle ? <ThemeToggle /> : null}
      </div>

      <div className="mt-8 space-y-6">{children}</div>

      {footer ? <div className="mt-8 border-t border-white/10 pt-6 text-sm text-foreground/70">{footer}</div> : null}
    </GlassPanel>
  );
}
