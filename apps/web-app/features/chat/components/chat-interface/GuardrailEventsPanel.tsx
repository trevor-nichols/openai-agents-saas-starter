import { Badge } from '@/components/ui/badge';
import { CodeBlock } from '@/components/ui/ai/code-block';
import { InlineTag } from '@/components/ui/foundation';
import type { StreamingChatEvent } from '@/lib/api/client/types.gen';

type GuardrailEventsPanelProps = {
  events: StreamingChatEvent[];
};

export function GuardrailEventsPanel({ events }: GuardrailEventsPanelProps) {
  const guardrailEvents = events.filter((evt) => evt.kind === 'guardrail_result');
  if (guardrailEvents.length === 0) return null;

  const booleanTag = (label: string, value: boolean | null | undefined) => {
    if (value === null || value === undefined) return null;
    return <InlineTag tone={value ? 'warning' : 'default'}>{`${label}: ${value ? 'yes' : 'no'}`}</InlineTag>;
  };

  return (
    <div className="space-y-3">
      {guardrailEvents.map((evt, idx) => {
        const confidence =
          evt.guardrail_confidence !== null && evt.guardrail_confidence !== undefined
            ? evt.guardrail_confidence
            : null;

        return (
          <div
            key={`${evt.guardrail_key ?? evt.guardrail_name ?? 'guardrail'}-${evt.response_id ?? idx}-${idx}`}
            className="rounded-lg border border-white/5 bg-white/5 p-3 shadow-sm"
          >
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline">Guardrail</Badge>
              {evt.guardrail_stage ? <InlineTag tone="default">Stage: {evt.guardrail_stage}</InlineTag> : null}
              {evt.guardrail_key ? <InlineTag tone="default">Key: {evt.guardrail_key}</InlineTag> : null}
              {evt.guardrail_name ? <InlineTag tone="default">Name: {evt.guardrail_name}</InlineTag> : null}
              {evt.guardrail_summary ? <InlineTag tone="default">Summary</InlineTag> : null}
              {booleanTag('Tripwire', evt.guardrail_tripwire_triggered)}
              {booleanTag('Flagged', evt.guardrail_flagged)}
              {booleanTag('Suppressed', evt.guardrail_suppressed)}
              {confidence !== null ? <InlineTag tone="default">Confidence: {confidence.toFixed(2)}</InlineTag> : null}
            </div>

            {evt.guardrail_masked_content ? (
              <div className="mt-2">
                <CodeBlock code={evt.guardrail_masked_content} language="text" />
              </div>
            ) : null}

            {evt.guardrail_details ? (
              <div className="mt-2">
                <CodeBlock code={JSON.stringify(evt.guardrail_details, null, 2)} language="json" />
              </div>
            ) : null}

            {evt.guardrail_token_usage ? (
              <div className="mt-2">
                <CodeBlock code={JSON.stringify(evt.guardrail_token_usage, null, 2)} language="json" />
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
