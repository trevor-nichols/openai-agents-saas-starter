import { useEffect } from 'react';
import { useReactFlow } from '@xyflow/react';

import { WORKFLOW_GRAPH_FIT_VIEW_OPTIONS } from '../constants';

export function useFitViewOnNodes(nodeCount: number, descriptorKey?: string | null) {
  const { fitView } = useReactFlow();

  useEffect(() => {
    if (!nodeCount) return;
    const handle = requestAnimationFrame(() => {
      fitView(WORKFLOW_GRAPH_FIT_VIEW_OPTIONS);
    });
    return () => cancelAnimationFrame(handle);
  }, [descriptorKey, fitView, nodeCount]);
}
