import { Tool, ToolContent, ToolHeader, ToolInput, ToolOutput } from '@/components/ui/ai/tool';
import type { ToolUIPart } from 'ai';

import { renderToolOutput } from '@/components/ui/ai/renderToolOutput';
import type { ToolState } from '@/lib/chat/types';

interface ToolEventsPanelProps {
  tools: ToolState[];
}

export function ToolEventsPanel({ tools }: ToolEventsPanelProps) {
  if (tools.length === 0) return null;

  return (
    <div className="space-y-3">
      {tools.map((tool) => (
        <Tool key={tool.id} defaultOpen={tool.status !== 'output-available'}>
          <ToolHeader type={`tool-${tool.name || 'call'}` as ToolUIPart['type']} state={tool.status} />
          <ToolContent>
            {tool.input ? <ToolInput input={tool.input} /> : null}
            <ToolOutput output={renderToolOutput(tool)} errorText={tool.errorText ?? undefined} />
          </ToolContent>
        </Tool>
      ))}
    </div>
  );
}
