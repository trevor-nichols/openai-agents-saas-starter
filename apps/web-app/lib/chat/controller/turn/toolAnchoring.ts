import type { ToolEventAnchors, ToolState } from '../../types';
import type { AssistantTurnMessage } from './turnRuntime';

export interface ComputeToolEventAnchorsParams {
  userAnchorId: string;
  assistantMessages: AssistantTurnMessage[];
  tools: ToolState[];
}

export function computeToolEventAnchors(params: ComputeToolEventAnchorsParams): ToolEventAnchors {
  const { userAnchorId, assistantMessages, tools } = params;

  const messageOrder = [...assistantMessages].sort((a, b) => a.outputIndex - b.outputIndex);
  const sortedTools = [...tools].sort(
    (a, b) =>
      (a.outputIndex ?? Number.POSITIVE_INFINITY) -
      (b.outputIndex ?? Number.POSITIVE_INFINITY),
  );

  const anchors: ToolEventAnchors = {};
  for (const tool of sortedTools) {
    const toolIndex = tool.outputIndex ?? Number.POSITIVE_INFINITY;
    let anchorId = userAnchorId;
    for (const msg of messageOrder) {
      if (msg.outputIndex < toolIndex) {
        anchorId = msg.uiId;
      } else {
        break;
      }
    }
    const ids = anchors[anchorId];
    if (ids) ids.push(tool.id);
    else anchors[anchorId] = [tool.id];
  }

  return anchors;
}

