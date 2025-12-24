export type WorkflowGraphNodeId = string;

export function workflowGraphNodeId(stageIndex: number, stepIndex: number): WorkflowGraphNodeId {
  return `${stageIndex}:${stepIndex}`;
}
