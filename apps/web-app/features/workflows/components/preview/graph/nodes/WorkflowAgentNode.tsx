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

export type WorkflowAgentNodeData = {
  title: string;
  agentKey: string;
  stageName: string;
  stageMode: 'sequential' | 'parallel';
  status: NodeStatus;
};

export type WorkflowAgentFlowNode = Node<WorkflowAgentNodeData, 'workflowAgent'>;

function statusTone(status: NodeStatus): 'secondary' | 'outline' | 'destructive' {
  if (status === 'success') return 'secondary';
  if (status === 'error') return 'destructive';
  return 'outline';
}

function toolTone(status: 'waiting' | 'running' | 'done' | 'error'): 'secondary' | 'outline' | 'destructive' {
  if (status === 'done') return 'secondary';
  if (status === 'error') return 'destructive';
  return 'outline';
}

export function WorkflowAgentNode({ id, data, selected }: NodeProps<WorkflowAgentFlowNode>) {
  const preview = useWorkflowNodePreview(id);

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

        <BaseNodeContent className="gap-3 px-4 py-4">
          <div className="flex items-center justify-between gap-2">
            <div className="text-sm font-semibold tracking-tight text-foreground">{statusTitle}</div>
            <div className="flex items-center gap-2">
              {preview.lifecycleStatus ? (
                <Badge variant="secondary" className="text-[10px] uppercase tracking-wide">
                  {preview.lifecycleStatus}
                </Badge>
              ) : null}
              <Badge variant={statusTone(data.status)} className="text-[10px] uppercase tracking-wide">
                {data.status}
              </Badge>
            </div>
          </div>

          {preview.items.length ? (
            <div className="grid gap-2">
              {preview.items.map((item) => {
                if (item.kind === 'tool') {
                  return (
                    <div key={item.itemId} className="rounded-md border border-border/60 bg-muted/20 px-2 py-1.5">
                      <div className="flex items-center justify-between gap-2">
                        <div className="min-w-0 truncate text-xs font-medium text-foreground/90" title={item.label}>
                          {item.label}
                        </div>
                        <Badge variant={toolTone(item.status)} className="text-[10px] uppercase tracking-wide">
                          {item.status}
                        </Badge>
                      </div>
                      {item.inputPreview ? (
                        <div className="mt-1 line-clamp-2 text-[11px] text-muted-foreground" title={item.inputPreview}>
                          {item.inputPreview}
                        </div>
                      ) : null}
                    </div>
                  );
                }

                if (item.kind === 'refusal') {
                  return (
                    <div key={item.itemId} className="rounded-md border border-destructive/30 bg-destructive/10 px-2 py-1.5">
                      <div className="line-clamp-3 whitespace-pre-wrap text-xs text-destructive/90">
                        {item.text}
                      </div>
                    </div>
                  );
                }

                return (
                  <div key={item.itemId} className="rounded-md border border-border/60 bg-muted/10 px-2 py-1.5">
                    <div className="line-clamp-3 whitespace-pre-wrap text-xs text-foreground/90">
                      {item.text}
                    </div>
                  </div>
                );
              })}

              {preview.overflowCount > 0 ? (
                <div className="text-[11px] text-muted-foreground">
                  +{preview.overflowCount} more…
                </div>
              ) : null}
            </div>
          ) : (
            <div className="text-sm text-muted-foreground">{statusDescription}</div>
          )}
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
