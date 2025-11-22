import type { Meta, StoryObj } from '@storybook/react';

import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from './carousel';

const meta: Meta<typeof Carousel> = {
  title: 'UI/Media/Carousel',
  component: Carousel,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof Carousel>;

const slides = [
  { title: 'Realtime chat', description: 'Streamed responses with citations.' },
  { title: 'Billing', description: 'Plans, usage, invoices.' },
  { title: 'Security', description: 'SAML, audit logs, key rotation.' },
  { title: 'Playground', description: 'Experiment with tools and agents.' },
];

export const Default: Story = {
  render: () => (
    <div className="flex w-full items-center justify-center">
      <Carousel className="max-w-xl">
        <CarouselContent>
          {slides.map((slide, idx) => (
            <CarouselItem key={slide.title} className="basis-full">
              <div className="rounded-xl border border-white/10 bg-white/5 p-6 shadow-sm">
                <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Slide {idx + 1}</p>
                <h3 className="mt-2 text-lg font-semibold">{slide.title}</h3>
                <p className="text-sm text-muted-foreground mt-1">{slide.description}</p>
              </div>
            </CarouselItem>
          ))}
        </CarouselContent>
        <CarouselPrevious />
        <CarouselNext />
      </Carousel>
    </div>
  ),
};
