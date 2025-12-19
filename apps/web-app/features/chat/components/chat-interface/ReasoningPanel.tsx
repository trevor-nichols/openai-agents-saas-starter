import { Reasoning, ReasoningContent, ReasoningTrigger } from '@/components/ui/ai/reasoning';
import { ReasoningParts } from '@/components/ui/ai/reasoning-parts';
import type { ReasoningPart } from '@/lib/streams/publicSseV1/reasoningParts';

interface ReasoningPanelProps {
  reasoningText?: string;
  reasoningParts?: ReasoningPart[];
  isStreaming: boolean;
}

export function ReasoningPanel({ reasoningText, reasoningParts, isStreaming }: ReasoningPanelProps) {
  const hasParts = Boolean(reasoningParts?.length);
  if (hasParts) {
    return <ReasoningParts parts={reasoningParts ?? []} isStreaming={isStreaming} defaultOpen />;
  }

  if (!reasoningText) return null;

  return (
    <Reasoning
      isStreaming={isStreaming}
      defaultOpen
      className="rounded-lg border border-white/5 bg-white/5 px-4 py-3"
    >
      <ReasoningTrigger title="Reasoning" />
      <ReasoningContent>{reasoningText}</ReasoningContent>
    </Reasoning>
  );
}
