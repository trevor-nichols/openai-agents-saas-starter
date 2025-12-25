import { AgentToolStream } from '@/components/ui/ai/agent-tool-stream';
import { Tool, ToolContent, ToolHeader, ToolInput, ToolOutput } from '@/components/ui/ai/tool';
import type { ToolUIPart } from 'ai';

import { renderToolOutput } from '@/components/ui/ai/renderToolOutput';
import type { ToolState } from '@/lib/chat/types';
import type { AgentToolStreamMap } from '@/lib/streams/publicSseV1/agentToolStreams';

interface ToolEventsPanelProps {
  tools: ToolState[];
  agentToolStreams?: AgentToolStreamMap;
}

export function ToolEventsPanel({ tools, agentToolStreams }: ToolEventsPanelProps) {
  if (tools.length === 0) return null;

  return (
    <div className="space-y-3">
      {tools.map((tool) => (
        <Tool key={tool.id} defaultOpen={tool.status !== 'output-available'}>
          <ToolHeader
            type={`tool-${tool.toolType === 'agent' ? `agent:${tool.name || 'call'}` : tool.name || 'call'}` as ToolUIPart['type']}
            state={tool.status}
          />
          <ToolContent>
            {tool.input ? <ToolInput input={tool.input} /> : null}
            {(() => {
              const agentStream = agentToolStreams?.[tool.id];
              if (!agentStream?.text) return null;
              return (
                <AgentToolStream
                  stream={agentStream}
                  isStreaming={tool.status === 'input-streaming' || tool.status === 'input-available'}
                />
              );
            })()}
            <ToolOutput output={renderToolOutput(tool)} errorText={tool.errorText ?? undefined} />
          </ToolContent>
        </Tool>
      ))}
    </div>
  );
}
