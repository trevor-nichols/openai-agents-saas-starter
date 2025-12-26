import { BackgroundVariant, MarkerType } from '@xyflow/react';

import { WORKFLOW_AGENT_NODE_WIDTH } from './nodes/workflowAgentNode.constants';

export const WORKFLOW_GRAPH_NODE_WIDTH = WORKFLOW_AGENT_NODE_WIDTH;
export const WORKFLOW_GRAPH_NODE_COL_PADDING = 80;
export const WORKFLOW_GRAPH_COL_GAP_X = WORKFLOW_GRAPH_NODE_WIDTH + WORKFLOW_GRAPH_NODE_COL_PADDING;
export const WORKFLOW_GRAPH_NODE_HEIGHT_ESTIMATE = 210;
export const WORKFLOW_GRAPH_PARALLEL_ROW_PADDING = 72;
export const WORKFLOW_GRAPH_PARALLEL_ROW_GAP_Y =
  WORKFLOW_GRAPH_NODE_HEIGHT_ESTIMATE + WORKFLOW_GRAPH_PARALLEL_ROW_PADDING;

export const WORKFLOW_GRAPH_DEFAULT_EDGE_OPTIONS = {
  type: 'smoothstep' as const,
  markerEnd: { type: MarkerType.ArrowClosed },
  style: {
    strokeWidth: 2,
  },
};

export const WORKFLOW_GRAPH_BACKGROUND = {
  variant: BackgroundVariant.Dots,
  gap: 24,
  size: 1,
  color: 'hsl(var(--border))',
  className: 'opacity-60',
};

export const WORKFLOW_GRAPH_FIT_VIEW_OPTIONS = {
  padding: 0.2,
  duration: 200,
};
