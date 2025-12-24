'use client';

import { cn } from '@/lib/utils';

type WorkflowGraphEmptyStateProps = {
  className?: string;
  variant?: 'panel' | 'centered';
};

export function WorkflowGraphEmptyState({
  className,
  variant = 'panel',
}: WorkflowGraphEmptyStateProps) {
  if (variant === 'centered') {
    return (
      <div className={cn('flex h-full w-full items-center justify-center p-6', className)}>
        <div className="rounded-lg border border-white/5 bg-white/5 p-4">
          <p className="text-sm text-foreground/70">Select a workflow to preview its structure.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('rounded-lg border border-white/5 bg-white/5 p-4', className)}>
      <p className="text-sm text-foreground/70">Select a workflow to preview its structure.</p>
    </div>
  );
}
