import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { CodeBlock } from '@/components/ui/ai/code-block';
import { SkeletonPanel, EmptyState } from '@/components/ui/states';
import { InlineTag } from '@/components/ui/foundation';
import type { WorkflowRunDetailView } from '@/lib/workflows/types';
import { workflowRunStatusVariant } from '../../../constants';

interface WorkflowRunDetailProps {
  run: WorkflowRunDetailView | null;
  isLoading?: boolean;
  onCancel?: () => void;
  canceling?: boolean;
}

export function WorkflowRunDetail({ run, isLoading, onCancel, canceling }: WorkflowRunDetailProps) {
  if (isLoading) {
    return <SkeletonPanel lines={6} />;
  }

  if (!run) {
    return <EmptyState title="Select a run" description="Pick a run from history to inspect details." />;
  }

  const statusVariant = workflowRunStatusVariant(run.status);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h3 className="text-sm font-semibold">Run {run.workflow_run_id}</h3>
        <Badge variant={statusVariant} className="capitalize">
          {run.status}
        </Badge>
        <InlineTag tone="default">Workflow: {run.workflow_key}</InlineTag>
        {run.conversation_id ? <InlineTag tone="default">Conversation: {run.conversation_id}</InlineTag> : null}
        {onCancel && run.status === 'running' ? (
          <Button size="sm" variant="outline" onClick={onCancel} disabled={canceling}>
            {canceling ? 'Canceling…' : 'Cancel run'}
          </Button>
        ) : null}
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <DetailItem label="Started" value={run.started_at} />
        <DetailItem label="Ended" value={run.ended_at ?? '—'} />
        <DetailItem label="User" value={run.user_id} />
        <DetailItem label="Final text" value={run.final_output_text ?? '—'} />
      </div>

      {run.final_output_structured ? (
        <div>
          <p className="text-xs font-semibold text-foreground/60 mb-1">Final structured output</p>
          <CodeBlock code={JSON.stringify(run.final_output_structured, null, 2)} language="json" />
        </div>
      ) : null}

      {run.output_schema ? (
        <div>
          <p className="text-xs font-semibold text-foreground/60 mb-1">Declared output schema</p>
          <CodeBlock code={JSON.stringify(run.output_schema, null, 2)} language="json" />
        </div>
      ) : null}

      <div className="space-y-2">
        <p className="text-xs font-semibold text-foreground/60">Steps</p>
        {run.steps.length === 0 ? (
          <p className="text-sm text-foreground/60">No step details captured.</p>
        ) : (
          <div className="space-y-2">
            {run.steps.map((step) => (
              <div key={step.response_id ?? step.name} className="rounded-md border border-white/5 bg-white/5 p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-semibold">{step.name}</span>
                  <InlineTag tone="default">Agent: {step.agent_key}</InlineTag>
                  {step.stage_name ? <InlineTag tone="default">Stage: {step.stage_name}</InlineTag> : null}
                  {step.parallel_group ? <InlineTag tone="default">Group: {step.parallel_group}</InlineTag> : null}
                </div>
                {step.response_text ? (
                  <p className="mt-1 text-sm text-foreground">{step.response_text}</p>
                ) : null}
                {step.structured_output ? (
                  <div className="mt-2">
                    <CodeBlock code={JSON.stringify(step.structured_output, null, 2)} language="json" />
                  </div>
                ) : null}
                {step.output_schema ? (
                  <div className="mt-2">
                    <p className="text-xs font-semibold text-foreground/60 mb-1">Step output schema</p>
                    <CodeBlock code={JSON.stringify(step.output_schema, null, 2)} language="json" />
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function DetailItem({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-white/5 bg-white/5 p-3 text-sm">
      <p className="text-xs uppercase tracking-wide text-foreground/50">{label}</p>
      <p className="text-foreground">{value}</p>
    </div>
  );
}
