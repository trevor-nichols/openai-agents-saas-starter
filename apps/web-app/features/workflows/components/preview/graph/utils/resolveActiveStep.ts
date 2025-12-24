import type { WorkflowDescriptor } from '@/lib/workflows/types';

import type { ResolvedActiveStep, WorkflowGraphActiveStep } from '../types';

export function resolveActiveStep(
  descriptor: WorkflowDescriptor | null,
  activeStep: WorkflowGraphActiveStep | null | undefined,
): ResolvedActiveStep | null {
  if (!descriptor?.stages?.length || !activeStep) return null;

  for (const [stageIndex, stage] of descriptor.stages.entries()) {
    for (const [stepIndex, step] of stage.steps.entries()) {
      const branchMatches =
        activeStep.branchIndex == null || activeStep.branchIndex === stepIndex;

      if (activeStep.stepName) {
        if (step.name === activeStep.stepName && branchMatches) {
          return { stageIndex, stepIndex };
        }
        continue;
      }

      if (activeStep.stageName) {
        if (stage.name === activeStep.stageName && branchMatches) {
          return { stageIndex, stepIndex };
        }
        continue;
      }

      if (activeStep.parallelGroup) {
        if (stage.name === activeStep.parallelGroup && branchMatches) {
          return { stageIndex, stepIndex };
        }
      }
    }
  }

  return null;
}
