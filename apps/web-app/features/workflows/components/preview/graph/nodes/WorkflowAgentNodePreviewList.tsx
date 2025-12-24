'use client';

import { Badge } from '@/components/ui/badge';
import type { WorkflowNodePreviewSnapshot } from '@/lib/workflows/streaming';
import { toolStatusTone } from './workflowAgentNode.constants';

type WorkflowAgentNodePreviewListProps = {
  preview: WorkflowNodePreviewSnapshot;
  statusDescription: string;
};

export function WorkflowAgentNodePreviewList({
  preview,
  statusDescription,
}: WorkflowAgentNodePreviewListProps) {
  if (!preview.items.length) {
    return <div className="text-sm text-muted-foreground">{statusDescription}</div>;
  }

  return (
    <div className="grid gap-2">
      {preview.items.map((item) => {
        if (item.kind === 'tool') {
          return (
            <div key={item.itemId} className="rounded-md border border-border/60 bg-muted/20 px-2 py-1.5">
              <div className="flex items-center justify-between gap-2">
                <div className="min-w-0 truncate text-xs font-medium text-foreground/90" title={item.label}>
                  {item.label}
                </div>
                <Badge variant={toolStatusTone(item.status)} className="text-[10px] uppercase tracking-wide">
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
        <div className="text-[11px] text-muted-foreground">+{preview.overflowCount} more…</div>
      ) : null}
    </div>
  );
}
