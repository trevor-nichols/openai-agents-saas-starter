import { GlassPanel } from '@/components/ui/foundation';

import type { ProofPoint } from '../types';

interface ProofPointsProps {
  items: ProofPoint[];
}

export function ProofPoints({ items }: ProofPointsProps) {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {items.map((item) => (
        <GlassPanel key={item.label} className="space-y-2 border border-white/10">
          <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">{item.label}</p>
          <p className="text-base text-foreground/80">{item.value}</p>
        </GlassPanel>
      ))}
    </div>
  );
}
