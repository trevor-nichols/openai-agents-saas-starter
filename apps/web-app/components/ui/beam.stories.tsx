import type { Meta, StoryObj } from '@storybook/react';
import { useRef } from 'react';

import { AnimatedBeam } from './beam';

const meta: Meta<typeof AnimatedBeam> = {
  title: 'UI/Media/Beam',
  component: AnimatedBeam,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof AnimatedBeam>;

const DefaultComponent = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const fromRef = useRef<HTMLDivElement>(null);
  const toRef = useRef<HTMLDivElement>(null);

  return (
    <div
      ref={containerRef}
      className="relative flex h-72 w-full max-w-3xl items-center justify-between rounded-xl border border-white/10 bg-white/5 p-6"
    >
      <div ref={fromRef} className="rounded-lg border border-white/10 bg-primary/20 px-4 py-3 text-sm font-semibold text-primary-foreground">
        Source
      </div>
      <div ref={toRef} className="rounded-lg border border-white/10 bg-emerald-500/20 px-4 py-3 text-sm font-semibold text-emerald-100">
        Destination
      </div>

      <AnimatedBeam
        containerRef={containerRef}
        fromRef={fromRef}
        toRef={toRef}
        curvature={60}
        pathColor="#60a5fa"
        gradientStartColor="#60a5fa"
        gradientStopColor="#22d3ee"
      />
    </div>
  );
};

export const Default: Story = {
  render: () => <DefaultComponent />,
};
