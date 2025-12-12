'use client';

import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';

import { SectionHeader } from '@/components/ui/foundation';

import { AgentCatalogGrid } from '../components/AgentCatalogGrid';
import { AgentToolsPanel } from '../components/AgentToolsPanel';
import { ContainerBindingsPanel } from '../components/ContainerBindingsPanel';
import { AGENT_WORKSPACE_COPY } from '../constants';
import { agentSummaries, sampleContainers, toolsByAgent, toolsSummary } from './fixtures';

type AgentWorkspacePreviewProps = {
  isLoading?: boolean;
  showError?: boolean;
};

function AgentWorkspacePreview({ isLoading = false, showError = false }: AgentWorkspacePreviewProps) {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(agentSummaries[0]?.name ?? null);
  const catalogPages =
    agentSummaries.length > 6
      ? [
          {
            items: agentSummaries.slice(0, 6),
            next_cursor: 'cursor-1',
            total: agentSummaries.length,
          },
          {
            items: agentSummaries.slice(6, 12),
            next_cursor: null,
            total: agentSummaries.length,
          },
        ]
      : [
          {
            items: agentSummaries,
            next_cursor: null,
            total: agentSummaries.length,
          },
        ];

  const toolsError = showError ? 'Tool registry unavailable' : null;
  const catalogError = showError ? 'Failed to load agents' : null;
  const containerError = showError ? new Error('Containers endpoint unavailable') : null;

  return (
    <section className="space-y-8">
      <SectionHeader
        eyebrow={AGENT_WORKSPACE_COPY.eyebrow}
        title={AGENT_WORKSPACE_COPY.title}
        description={AGENT_WORKSPACE_COPY.description}
      />

      <div className="grid gap-8 xl:grid-cols-[minmax(520px,1.1fr)_minmax(480px,1fr)]">
        <AgentCatalogGrid
          agentsPages={catalogPages}
          visiblePageIndex={0}
          totalAgents={agentSummaries.length}
          hasNextPage={catalogPages.length > 1}
          hasPrevPage={false}
          isFetchingNextPage={false}
          toolsByAgent={toolsByAgent}
          summary={toolsSummary}
          isLoadingAgents={isLoading}
          isLoadingTools={isLoading}
          errorMessage={catalogError}
          onNextPage={() => console.log('next page')}
          onPrevPage={() => console.log('prev page')}
          onPageSelect={(pageIndex: number) => console.log('select page', pageIndex)}
          onRefreshTools={() => console.log('refresh tools')}
          onRefreshAgents={() => console.log('refresh agents')}
          selectedAgent={selectedAgent}
          onSelectAgent={setSelectedAgent}
        />

        <AgentToolsPanel
          summary={toolsSummary}
          toolsByAgent={toolsByAgent}
          selectedAgent={selectedAgent}
          isLoading={isLoading}
          error={toolsError}
          onRefresh={() => console.log('refresh tools')}
        />
      </div>

      <ContainerBindingsPanel
        containers={sampleContainers}
        isLoading={isLoading}
        error={containerError}
        selectedContainerId={sampleContainers[0]?.id ?? null}
        onSelect={(id) => console.log('select container', id)}
        onCreate={(name, memory) => console.log('create container', { name, memory })}
        onDelete={(id) => console.log('delete container', id)}
        onBind={(id) => console.log('bind container', id)}
        onUnbind={() => console.log('unbind container')}
        agentKey={selectedAgent ?? 'triage_agent'}
      />
    </section>
  );
}

const meta: Meta<typeof AgentWorkspacePreview> = {
  title: 'Agents/Page',
  component: AgentWorkspacePreview,
};

export default meta;

type Story = StoryObj<typeof AgentWorkspacePreview>;

export const Default: Story = {};

export const Loading: Story = {
  args: {
    isLoading: true,
  },
};

export const ErrorState: Story = {
  args: {
    showError: true,
  },
};
