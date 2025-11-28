import { SkeletonPanel, EmptyState } from '@/components/ui/states';
import { Badge } from '@/components/ui/badge';
import { CodeBlock } from '@/components/ui/ai/code-block';
import type { WorkflowDescriptor } from '@/lib/workflows/types';

interface WorkflowDescriptorCardProps {
  descriptor: WorkflowDescriptor | null;
  isLoading?: boolean;
}

export function WorkflowDescriptorCard({ descriptor, isLoading }: WorkflowDescriptorCardProps) {
  if (isLoading) {
    return <SkeletonPanel lines={4} />;
  }

  if (!descriptor) {
    return <EmptyState title="No workflow selected" description="Pick a workflow to view its details." />;
  }

  const primaryStage = descriptor.stages?.[0];

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold leading-tight">{descriptor.display_name}</h3>
          <p className="text-xs text-foreground/60">{descriptor.description}</p>
        </div>
        {descriptor.default ? <Badge variant="outline">Default</Badge> : null}
      </div>

      <div className="flex flex-wrap gap-2 text-xs text-foreground/70">
        <Badge variant="secondary" className="capitalize">
          Steps: {descriptor.step_count}
        </Badge>
        <Badge variant={descriptor.allow_handoff_agents ? 'outline' : 'secondary'}>
          {descriptor.allow_handoff_agents ? 'Handoffs enabled' : 'Handoffs off'}
        </Badge>
        {primaryStage ? (
          <Badge variant="outline" className="capitalize">
            Stage: {primaryStage.name} ({primaryStage.mode})
          </Badge>
        ) : null}
      </div>

      {descriptor.output_schema ? (
        <div className="space-y-1">
          <p className="text-xs font-semibold text-foreground/60">Output schema</p>
          <CodeBlock code={JSON.stringify(descriptor.output_schema, null, 2)} language="json" />
        </div>
      ) : null}
    </div>
  );
}
