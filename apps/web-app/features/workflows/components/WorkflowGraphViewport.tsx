'use client';

import { useCallback, useRef, useState, type WheelEvent } from 'react';
import { ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';
import { motion, useMotionValue } from 'framer-motion';

import { Button } from '@/components/ui/button';
import { InlineTag } from '@/components/ui/foundation';
import { cn } from '@/lib/utils';
import type { WorkflowDescriptor } from '@/lib/workflows/types';

import { WorkflowGraph } from './WorkflowGraph';

const MIN_SCALE = 0.6;
const MAX_SCALE = 2.2;
const ZOOM_STEP = 0.12;

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

interface WorkflowGraphViewportProps {
  descriptor: WorkflowDescriptor | null;
  activeStep?: {
    stepName?: string | null;
    stageName?: string | null;
    parallelGroup?: string | null;
    branchIndex?: number | null;
  } | null;
  className?: string;
}

export function WorkflowGraphViewport({ descriptor, activeStep, className }: WorkflowGraphViewportProps) {
  const scale = useMotionValue(1);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const viewportRef = useRef<HTMLDivElement | null>(null);
  const [zoomPct, setZoomPct] = useState(100);
  const zoomLabel = `${zoomPct}%`;

  const setScale = useCallback(
    (next: number) => {
      const clamped = clamp(next, MIN_SCALE, MAX_SCALE);
      scale.set(clamped);
      setZoomPct(Math.round(clamped * 100));
    },
    [scale],
  );

  const zoomIn = useCallback(() => setScale(scale.get() + ZOOM_STEP), [scale, setScale]);
  const zoomOut = useCallback(() => setScale(scale.get() - ZOOM_STEP), [scale, setScale]);
  const reset = useCallback(() => {
    scale.set(1);
    x.set(0);
    y.set(0);
    setZoomPct(100);
  }, [scale, x, y]);

  const handleWheel = useCallback(
    (event: WheelEvent) => {
      const shouldZoom = event.ctrlKey || event.metaKey;
      if (!shouldZoom) return;
      event.preventDefault();
      const direction = event.deltaY > 0 ? -1 : 1;
      const next = scale.get() + direction * ZOOM_STEP;
      setScale(next);
    },
    [scale, setScale],
  );

  return (
    <div
      ref={viewportRef}
      onDoubleClick={reset}
      onWheel={handleWheel}
      className={cn('relative h-full w-full overflow-hidden', className)}
    >
      <div className="absolute right-4 top-4 z-10 flex items-center gap-2">
        <InlineTag tone="default" className="bg-background/60">
          {zoomLabel}
        </InlineTag>
        <Button size="icon" variant="outline" onClick={zoomOut} title="Zoom out" type="button">
          <ZoomOut className="h-4 w-4" />
        </Button>
        <Button size="icon" variant="outline" onClick={zoomIn} title="Zoom in" type="button">
          <ZoomIn className="h-4 w-4" />
        </Button>
        <Button size="icon" variant="outline" onClick={reset} title="Reset view" type="button">
          <RotateCcw className="h-4 w-4" />
        </Button>
      </div>

      <div className="absolute inset-0 flex items-center justify-center p-6">
        <motion.div
          style={{ x, y, scale }}
          drag
          dragMomentum={false}
          className="cursor-grab active:cursor-grabbing"
        >
          <WorkflowGraph
            descriptor={descriptor}
            activeStep={activeStep}
            className="w-full max-w-5xl border-none bg-transparent shadow-none"
          />
        </motion.div>
      </div>
    </div>
  );
}
