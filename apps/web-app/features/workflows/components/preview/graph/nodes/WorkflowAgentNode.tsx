'use client';

import { Handle, Position, type Node, type NodeProps } from '@xyflow/react';
import { Rocket } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import {
  BaseNode,
  BaseNodeContent,
  BaseNodeFooter,
  BaseNodeHeader,
  BaseNodeHeaderTitle,
  NodeStatusIndicator,
  type NodeStatus,
} from '@/components/ui/workflow';
import { useWorkflowNodePreview } from '../nodeStreamContext';
import { cn } from '@/lib/utils';
import type { ContainerResponse, VectorStoreResponse } from '@/lib/api/client/types.gen';
import { WorkflowAgentNodeConfigPopover } from './WorkflowAgentNodeConfigPopover';
import { WorkflowAgentNodePreviewList } from './WorkflowAgentNodePreviewList';
import { WORKFLOW_AGENT_NODE_STATUS_META, WORKFLOW_AGENT_NODE_WIDTH } from './workflowAgentNode.constants';

export type WorkflowAgentNodeData = {
  title: string;
  agentKey: string;
  stageName: string;
  stageMode: 'sequential' | 'parallel';
  status: NodeStatus;
  tools: string[];
  supportsContainers: boolean;
  supportsFileSearch: boolean;
  containers: ContainerResponse[];
  containersError: string | null;
  isLoadingContainers: boolean;
  selectedContainerId: string | null;
  onContainerOverrideChange?: (agentKey: string, containerId: string | null) => void;
  vectorStores: VectorStoreResponse[];
  vectorStoresError: string | null;
  isLoadingVectorStores: boolean;
  selectedVectorStoreId: string | null;
  onVectorStoreOverrideChange?: (agentKey: string, vectorStoreId: string | null) => void;
};

export type WorkflowAgentFlowNode = Node<WorkflowAgentNodeData, 'workflowAgent'>;

export function WorkflowAgentNode({ id, data, selected }: NodeProps<WorkflowAgentFlowNode>) {
  const preview = useWorkflowNodePreview(id);
  const statusMeta = WORKFLOW_AGENT_NODE_STATUS_META[data.status];

  return (
    <NodeStatusIndicator status={data.status} variant="border">
      <BaseNode
        className={cn(
          'group overflow-hidden shadow-sm',
          selected ? 'ring-1 ring-ring' : null,
        )}
        style={{ width: WORKFLOW_AGENT_NODE_WIDTH }}
      >
        <Handle
          type="target"
          position={Position.Left}
          className="!h-2.5 !w-2.5 !border-2 !border-background !bg-muted-foreground/70 !opacity-0 group-hover:!opacity-100 transition-opacity"
        />
        <Handle
          type="source"
          position={Position.Right}
          className="!h-2.5 !w-2.5 !border-2 !border-background !bg-muted-foreground/70 !opacity-0 group-hover:!opacity-100 transition-opacity"
        />

        <BaseNodeHeader className="px-4 py-3">
          <div className="flex min-w-0 items-center gap-2">
            <Rocket className="h-4 w-4 flex-shrink-0 text-muted-foreground" aria-hidden="true" />
            <BaseNodeHeaderTitle className="truncate text-base" title={data.title}>
              {data.title}
            </BaseNodeHeaderTitle>
          </div>
          <div className="flex items-center gap-2">
            <WorkflowAgentNodeConfigPopover
              agentKey={data.agentKey}
              tools={data.tools}
              supportsContainers={data.supportsContainers}
              supportsFileSearch={data.supportsFileSearch}
              containers={data.containers}
              containersError={data.containersError}
              isLoadingContainers={data.isLoadingContainers}
              selectedContainerId={data.selectedContainerId}
              onContainerOverrideChange={data.onContainerOverrideChange}
              vectorStores={data.vectorStores}
              vectorStoresError={data.vectorStoresError}
              isLoadingVectorStores={data.isLoadingVectorStores}
              selectedVectorStoreId={data.selectedVectorStoreId}
              onVectorStoreOverrideChange={data.onVectorStoreOverrideChange}
            />

            <Badge variant="secondary" className="shrink-0 text-xs">
              {data.stageMode}
            </Badge>
          </div>
        </BaseNodeHeader>

        <div className="h-px w-full bg-border/60" />

        <BaseNodeContent className="gap-3 px-4 py-4">
          <div className="flex items-center justify-between gap-2">
            <div className="text-sm font-semibold tracking-tight text-foreground">
              {statusMeta.title}
            </div>
            <div className="flex items-center gap-2">
              {preview.lifecycleStatus ? (
                <Badge variant="secondary" className="text-[10px] uppercase tracking-wide">
                  {preview.lifecycleStatus}
                </Badge>
              ) : null}
              <Badge variant={statusMeta.badgeTone} className="text-[10px] uppercase tracking-wide">
                {data.status}
              </Badge>
            </div>
          </div>
          <WorkflowAgentNodePreviewList preview={preview} statusDescription={statusMeta.description} />
        </BaseNodeContent>

        <BaseNodeFooter className="flex-row items-center justify-between gap-3 px-4 py-3">
          <span className="min-w-0 truncate text-xs font-mono text-foreground/80" title={data.agentKey}>
            {data.agentKey}
          </span>
          <span className="min-w-0 truncate text-xs text-muted-foreground" title={data.stageName}>
            {data.stageName}
          </span>
        </BaseNodeFooter>
      </BaseNode>
    </NodeStatusIndicator>
  );
}
