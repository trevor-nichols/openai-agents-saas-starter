import { GlassPanel, SectionHeader } from '@/components/ui/foundation';
import type { WorkflowDescriptorResponse, WorkflowSummary } from '@/lib/api/client/types.gen';
import { WorkflowDescriptorCard } from './WorkflowDescriptorCard';
import { WorkflowList } from './WorkflowList';

interface Props {
  workflows: WorkflowSummary[];
  isLoadingWorkflows: boolean;
  selectedKey: string | null;
  onSelect: (workflowKey: string) => void;
  descriptor: WorkflowDescriptorResponse | null;
  isLoadingDescriptor: boolean;
}

export function WorkflowSidebar({
  workflows,
  isLoadingWorkflows,
  selectedKey,
  onSelect,
  descriptor,
  isLoadingDescriptor,
}: Props) {
  return (
    <div className="space-y-3">
      <SectionHeader title="Workflows" description="Run multi-step workflows with streaming output." />
      <GlassPanel className="space-y-4 p-4">
        <WorkflowList items={workflows} isLoading={isLoadingWorkflows} selectedKey={selectedKey} onSelect={onSelect} />
        <div className="border-t border-white/5 pt-3">
          <WorkflowDescriptorCard descriptor={descriptor} isLoading={isLoadingDescriptor} />
        </div>
      </GlassPanel>
    </div>
  );
}
