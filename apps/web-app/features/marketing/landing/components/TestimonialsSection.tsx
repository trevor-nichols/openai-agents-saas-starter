"use client";

import { AnimatedTestimonials, type Testimonial } from '@/components/ui/testimonials';
import { SectionHeader } from '@/components/ui/foundation';

interface TestimonialsSectionProps {
  testimonials: Testimonial[];
}

export function TestimonialsSection({ testimonials }: TestimonialsSectionProps) {
  if (!testimonials.length) return null;

  return (
    <section className="relative w-full rounded-3xl bg-background/40 px-6 py-16">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_20%_20%,rgba(100,108,255,0.18),transparent_45%),radial-gradient(circle_at_80%_60%,rgba(99,223,255,0.12),transparent_40%)]" />
      <div className="relative mx-auto w-full max-w-6xl space-y-10">
        <SectionHeader
          eyebrow="Customer voice"
          title="Teams launch faster and pass enterprise checks sooner"
          description="Product, platform, and operations leaders explain why they cloned the starter."
        />
        <AnimatedTestimonials testimonials={testimonials} autoplay className="bg-transparent w-full max-w-6xl px-0" />
      </div>
    </section>
  );
}
