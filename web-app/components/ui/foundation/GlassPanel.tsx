import * as React from 'react';

import { cn } from '@/lib/utils';

export type GlassPanelProps = React.HTMLAttributes<HTMLDivElement>;

export const GlassPanel = React.forwardRef<HTMLDivElement, GlassPanelProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'rounded-lg border border-white/10 bg-white/5 p-6 shadow-glass backdrop-blur-glass transition duration-surface ease-apple',
        className
      )}
      {...props}
    />
  )
);

GlassPanel.displayName = 'GlassPanel';
