import * as React from 'react';

import { cn } from '@/lib/utils';

export type GlassPanelProps = React.HTMLAttributes<HTMLDivElement>;

export const GlassPanel = React.forwardRef<HTMLDivElement, GlassPanelProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'rounded-3xl border border-white/10 bg-glass p-8 shadow-xl backdrop-blur-xl transition-all duration-surface ease-apple hover:bg-glass-strong hover:shadow-2xl',
        className
      )}
      {...props}
    />
  )
);

GlassPanel.displayName = 'GlassPanel';
