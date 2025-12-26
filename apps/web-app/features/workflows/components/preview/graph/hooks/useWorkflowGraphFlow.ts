import { useMemo } from 'react';

import type { WorkflowDescriptor } from '@/lib/workflows/types';

import type { WorkflowGraphActiveStep, WorkflowGraphNodeDataOptions } from '../types';
import { buildWorkflowFlow } from '../utils/buildWorkflowFlow';
import { resolveActiveStep } from '../utils/resolveActiveStep';

export function useWorkflowGraphFlow(
  descriptor: WorkflowDescriptor | null,
  activeStep: WorkflowGraphActiveStep | null | undefined,
  options: WorkflowGraphNodeDataOptions,
) {
  const resolvedActiveStep = useMemo(
    () => resolveActiveStep(descriptor, activeStep),
    [descriptor, activeStep],
  );

  const flow = useMemo(
    () => buildWorkflowFlow(descriptor, resolvedActiveStep, options),
    [descriptor, resolvedActiveStep, options],
  );

  return { flow, activeStep: resolvedActiveStep };
}
