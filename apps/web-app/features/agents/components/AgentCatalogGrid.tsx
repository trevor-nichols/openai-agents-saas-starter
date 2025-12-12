// File Path: features/agents/components/AgentCatalogGrid.tsx
// Description: Presentational grid showing agent health + tooling context.

'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { InlineTag, SectionHeader } from '@/components/ui/foundation';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import { Carousel, CarouselContent, CarouselItem, type CarouselApi } from '@/components/ui/carousel';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import type { AgentListResponse } from '@/lib/api/client/types.gen';

import { AgentCatalogCard } from './AgentCatalogCard';
import type { ToolRegistrySummary, ToolsByAgentMap } from '../types';

interface AgentCatalogGridProps {
  agentsPages: AgentListResponse[];
  visiblePageIndex: number;
  totalAgents: number;
  hasNextPage: boolean;
  hasPrevPage: boolean;
  isFetchingNextPage: boolean;
  isLoadingAgents: boolean;
  isLoadingTools: boolean;
  errorMessage: string | null;
  onNextPage: () => void | Promise<void>;
  onPrevPage: () => void | Promise<void>;
  onPageSelect: (pageIndex: number) => void;
  onRefreshTools: () => void | Promise<void>;
  onRefreshAgents: () => void | Promise<void>;
  toolsByAgent: ToolsByAgentMap;
  summary: ToolRegistrySummary;
  selectedAgent: string | null;
  onSelectAgent: (agentName: string) => void;
}

export function AgentCatalogGrid({
  agentsPages,
  visiblePageIndex,
  totalAgents,
  hasNextPage,
  hasPrevPage,
  isFetchingNextPage,
  isLoadingAgents,
  isLoadingTools,
  errorMessage,
  onNextPage,
  onPrevPage,
  onPageSelect,
  onRefreshTools,
  onRefreshAgents,
  toolsByAgent,
  summary: _summary,
  selectedAgent,
  onSelectAgent,
}: AgentCatalogGridProps) {
  const [carouselApi, setCarouselApi] = useState<CarouselApi | null>(null);

  const pageCount = agentsPages.length;
  const pageLabel = pageCount ? `${visiblePageIndex + 1}/${pageCount}${hasNextPage ? '+' : ''}` : '1/1';
  const isLoading = isLoadingAgents || isLoadingTools;

  useEffect(() => {
    if (!carouselApi) {
      return;
    }
    carouselApi.scrollTo(Math.min(visiblePageIndex, Math.max(pageCount - 1, 0)), true);
  }, [carouselApi, pageCount, visiblePageIndex]);

  useEffect(() => {
    if (!carouselApi) {
      return;
    }
    const handleSelect = () => {
      const idx = carouselApi.selectedScrollSnap();
      onPageSelect(idx);
    };
    carouselApi.on('select', handleSelect);
    return () => {
      carouselApi.off('select', handleSelect);
    };
  }, [carouselApi, onPageSelect]);

  const renderedPages = useMemo(() => {
    if (pageCount === 0) {
      return [];
    }
    return agentsPages;
  }, [agentsPages, pageCount]);

  if (isLoading) {
    return <SkeletonPanel lines={8} />;
  }

  const hasRenderablePages = renderedPages.length > 0 && totalAgents > 0;

  if (errorMessage && !hasRenderablePages) {
    return (
      <ErrorState
        title="Unable to load agent catalog"
        message={errorMessage}
        onRetry={() => {
          void onRefreshAgents();
          void onRefreshTools();
        }}
      />
    );
  }

  if (totalAgents === 0) {
    return (
      <EmptyState
        title="No agents registered yet"
        description="Provision your first agent via the CLI or API, then refresh this page to see live telemetry."
        action={<Button disabled>Create agent</Button>}
      />
    );
  }

  if (!renderedPages.length) {
    return <SkeletonPanel lines={8} />;
  }

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Automation"
        title="Agent catalog"
        description="Inspect active agents, review their telemetry, and route chats with confidence."
        actions={
          <div className="flex flex-wrap items-center gap-3">
            <InlineTag tone={totalAgents ? 'positive' : 'default'}>
              {`${totalAgents} agent${totalAgents === 1 ? '' : 's'}`}
            </InlineTag>
            <InlineTag tone="default">Page {pageLabel}</InlineTag>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                void onRefreshAgents();
              }}
              disabled={isLoadingAgents}
            >
              Refresh agents
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                void onRefreshTools();
              }}
              disabled={isLoadingTools}
            >
              Refresh tools
            </Button>
            <Button variant="outline" size="sm" asChild>
              <Link href="/chat">Open workspace</Link>
            </Button>
            <Button size="sm" disabled>
              Create agent
            </Button>
          </div>
        }
      />

      {errorMessage ? (
        <Alert variant="destructive">
          <AlertTitle>Some pages failed to load</AlertTitle>
          <AlertDescription className="flex flex-wrap items-center gap-3">
            <span>{errorMessage}</span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                void onRefreshAgents();
              }}
              disabled={isLoadingAgents || isFetchingNextPage}
            >
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      ) : null}

      <div className="relative">
        <Carousel
          setApi={setCarouselApi}
          opts={{ align: 'start', loop: false, watchDrag: true }}
          className="px-1"
        >
          <CarouselContent className="gap-0">
            {renderedPages.map((page, idx) => (
              <CarouselItem key={`agent-page-${idx}`}>
                <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
                  {(page.items ?? []).map((agent) => (
                    <AgentCatalogCard
                      key={agent.name}
                      agent={agent}
                      tools={toolsByAgent[agent.name] ?? []}
                      isSelected={selectedAgent === agent.name}
                      onSelect={onSelectAgent}
                    />
                  ))}
                </div>
              </CarouselItem>
            ))}
          </CarouselContent>
        </Carousel>

        <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-sm text-foreground/70">
            <span>
              Page {visiblePageIndex + 1} of {pageCount || 1}
              {hasNextPage ? '+' : ''}
            </span>
            {isFetchingNextPage ? <Loader2 className="h-4 w-4 animate-spin text-foreground/60" /> : null}
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => onPrevPage()} disabled={!hasPrevPage}>
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onNextPage()}
              disabled={!hasNextPage && visiblePageIndex >= pageCount - 1}
            >
              Next
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
