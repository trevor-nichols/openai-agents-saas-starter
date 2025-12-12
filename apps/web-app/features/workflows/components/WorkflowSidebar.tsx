import { ScrollArea } from '@/components/ui/scroll-area';
import { SectionHeader } from '@/components/ui/foundation';
import type { WorkflowSummary } from '@/lib/api/client/types.gen';
import { WorkflowList } from './WorkflowList';

interface Props {
  workflows: WorkflowSummary[];
  isLoadingWorkflows: boolean;
  selectedKey: string | null;
  onSelect: (workflowKey: string) => void;
}

export function WorkflowSidebar({
  workflows,
  isLoadingWorkflows,
  selectedKey,
  onSelect,
}: Props) {
  return (
    <div className="flex h-full flex-col">
      <div className="p-4 pb-2">
        <SectionHeader title="Library" description="Select a workflow to configure." size="compact" />
      </div>
      <ScrollArea className="flex-1">
        <div className="p-4 pt-0">
            <WorkflowList items={workflows} isLoading={isLoadingWorkflows} selectedKey={selectedKey} onSelect={onSelect} />
        </div>
      </ScrollArea>
    </div>
  );
}
