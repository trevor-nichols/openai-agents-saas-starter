import { Reasoning, ReasoningContent, ReasoningTrigger } from '@/components/ui/ai/reasoning';

interface ReasoningPanelProps {
  reasoningText?: string;
  isStreaming: boolean;
}

export function ReasoningPanel({ reasoningText, isStreaming }: ReasoningPanelProps) {
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
