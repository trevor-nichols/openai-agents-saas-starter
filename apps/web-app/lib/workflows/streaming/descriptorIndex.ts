import type { StreamingWorkflowEvent, WorkflowDescriptorResponse } from '@/lib/api/client/types.gen';

import {
  serializeStageAgentBranchKey,
  serializeStageBranchKey,
  serializeWorkflowNodeIdentity,
  contextKeyFromWorkflowContext,
  type SerializedWorkflowNodeIdentity,
  type WorkflowNodeIdentity,
} from './stepKey';

export type WorkflowGraphNodeId = string;

export type WorkflowDescriptorIndex = Readonly<{
  workflowKey: string;
  nodeIdByIdentity: Map<SerializedWorkflowNodeIdentity, WorkflowGraphNodeId>;
  nodeIdByStageBranch: Map<string, WorkflowGraphNodeId>;
  nodeIdByStageAgentBranch: Map<string, WorkflowGraphNodeId>;
  knownNodeIds: Set<WorkflowGraphNodeId>;
}>;

function nodeIdFor(stageIndex: number, stepIndex: number): WorkflowGraphNodeId {
  // Keep consistent with WorkflowGraphViewport stepKey()
  return `${stageIndex}:${stepIndex}`;
}

export function buildWorkflowDescriptorIndex(descriptor: WorkflowDescriptorResponse): WorkflowDescriptorIndex {
  const nodeIdByIdentity = new Map<SerializedWorkflowNodeIdentity, WorkflowGraphNodeId>();
  const nodeIdByStageBranch = new Map<string, WorkflowGraphNodeId>();
  const nodeIdByStageAgentBranch = new Map<string, WorkflowGraphNodeId>();
  const knownNodeIds = new Set<WorkflowGraphNodeId>();

  descriptor.stages.forEach((stage, stageIndex) => {
    stage.steps.forEach((step, stepIndex) => {
      const branchIndex = stage.mode === 'parallel' ? stepIndex : null;
      const nodeId = nodeIdFor(stageIndex, stepIndex);
      knownNodeIds.add(nodeId);

      const identity: WorkflowNodeIdentity = {
        stageName: stage.name,
        stepName: step.name,
        branchIndex,
      };

      nodeIdByIdentity.set(serializeWorkflowNodeIdentity(identity), nodeId);
      // Only safe to use stage+branch fallback when branchIndex is present (parallel fan-out).
      if (branchIndex !== null) {
        nodeIdByStageBranch.set(serializeStageBranchKey({ stageName: stage.name, branchIndex }), nodeId);
      }
      nodeIdByStageAgentBranch.set(
        serializeStageAgentBranchKey({ stageName: stage.name, stepAgent: step.agent_key, branchIndex }),
        nodeId,
      );
    });
  });

  return {
    workflowKey: descriptor.key,
    nodeIdByIdentity,
    nodeIdByStageBranch,
    nodeIdByStageAgentBranch,
    knownNodeIds,
  };
}

export function resolveWorkflowNodeIdForEvent(
  index: WorkflowDescriptorIndex,
  event: StreamingWorkflowEvent,
): WorkflowGraphNodeId | null {
  const ctxKey = contextKeyFromWorkflowContext(event.workflow);
  if (!ctxKey) return null;

  const workflowKey = event.workflow?.workflow_key ?? null;
  if (workflowKey && workflowKey !== index.workflowKey) return null;

  const byExact = index.nodeIdByIdentity.get(
    serializeWorkflowNodeIdentity({
      stageName: ctxKey.stageName,
      stepName: ctxKey.stepName,
      branchIndex: ctxKey.branchIndex,
    }),
  );
  if (byExact) return byExact;

  if (ctxKey.stepAgent) {
    const byAgent = index.nodeIdByStageAgentBranch.get(
      serializeStageAgentBranchKey({
        stageName: ctxKey.stageName,
        stepAgent: ctxKey.stepAgent,
        branchIndex: ctxKey.branchIndex,
      }),
    );
    if (byAgent) return byAgent;
  }

  if (ctxKey.branchIndex !== null) {
    const byStageBranch = index.nodeIdByStageBranch.get(
      serializeStageBranchKey({ stageName: ctxKey.stageName, branchIndex: ctxKey.branchIndex }),
    );
    if (byStageBranch) return byStageBranch;
  }

  return null;
}
