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
import { cn } from '@/lib/utils';

export type WorkflowAgentNodeData = {
  title: string;
  agentKey: string;
  stageName: string;
  stageMode: 'sequential' | 'parallel';
  status: NodeStatus;
};

export type WorkflowAgentFlowNode = Node<WorkflowAgentNodeData, 'workflowAgent'>;

export function WorkflowAgentNode({ data, selected }: NodeProps<WorkflowAgentFlowNode>) {
  const statusTitle = (() => {
    switch (data.status) {
      case 'loading':
        return 'Running…';
      case 'success':
        return 'Completed';
      case 'error':
        return 'Error';
      case 'initial':
      default:
        return 'Ready';
    }
  })();

  const statusDescription = (() => {
    switch (data.status) {
      case 'loading':
        return 'Streaming output will appear here.';
      case 'success':
        return 'This step finished successfully.';
      case 'error':
        return 'This step failed.';
      case 'initial':
      default:
        return 'Awaiting execution.';
    }
  })();

  return (
    <NodeStatusIndicator status={data.status} variant="border">
      <BaseNode
        className={cn(
          'group w-[360px] overflow-hidden shadow-sm',
          selected ? 'ring-1 ring-ring' : null,
        )}
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
          <Badge variant="secondary" className="shrink-0 text-xs">
            {data.stageMode}
          </Badge>
        </BaseNodeHeader>

        <div className="h-px w-full bg-border/60" />

        <BaseNodeContent className="gap-2 px-4 py-5">
          <div className="text-3xl font-semibold tracking-tight text-foreground">{statusTitle}</div>
          <div className="text-sm text-muted-foreground">{statusDescription}</div>
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
