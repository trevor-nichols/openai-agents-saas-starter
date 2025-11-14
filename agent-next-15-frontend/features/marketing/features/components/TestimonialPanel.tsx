import { GlassPanel } from '@/components/ui/foundation';

import type { Testimonial } from '../types';

interface TestimonialPanelProps {
  testimonial: Testimonial;
}

export function TestimonialPanel({ testimonial }: TestimonialPanelProps) {
  return (
    <GlassPanel className="space-y-4 border border-white/10">
      <p className="text-lg italic text-foreground/80">{testimonial.quote}</p>
      <div>
        <p className="font-semibold text-foreground">{testimonial.author}</p>
        <p className="text-sm text-foreground/60">{testimonial.role}</p>
      </div>
    </GlassPanel>
  );
}
