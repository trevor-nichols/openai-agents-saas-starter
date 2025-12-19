// File Path: features/agents/components/AgentCatalogGrid.tsx
// Description: Presentational grid showing agent health + tooling context.

'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { ChevronLeft, ChevronRight, Loader2, Plus, RefreshCw } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { InlineTag } from '@/components/ui/foundation';
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
        description="Provision your first agent via the CLI or API."
        action={<Button disabled>Create agent</Button>}
      />
    );
  }

  if (!renderedPages.length) {
    return <SkeletonPanel lines={8} />;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-foreground">Available Agents</h3>
          <InlineTag tone={totalAgents ? 'positive' : 'default'}>
            {totalAgents}
          </InlineTag>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={() => {
              void onRefreshAgents();
              void onRefreshTools();
            }}
            disabled={isLoadingAgents}
            title="Refresh"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
          <Button variant="ghost" size="icon" className="h-7 w-7" asChild title="Open full workspace">
            <Link href="/chat">
              <Plus className="h-3.5 w-3.5" />
            </Link>
          </Button>
        </div>
      </div>

      {errorMessage ? (
        <Alert variant="destructive">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription className="text-xs">{errorMessage}</AlertDescription>
        </Alert>
      ) : null}

      <div className="relative">
        <Carousel
          setApi={setCarouselApi}
          opts={{ align: 'start', loop: false, watchDrag: true }}
          className="w-full"
        >
          <CarouselContent className="gap-0 ml-0">
            {renderedPages.map((page, idx) => (
              <CarouselItem key={`agent-page-${idx}`} className="pl-0">
                <div className="flex flex-col gap-3">
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

        {(hasPrevPage || hasNextPage) && (
          <div className="mt-4 flex items-center justify-center gap-2">
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8 rounded-full"
              onClick={() => onPrevPage()}
              disabled={!hasPrevPage}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-xs text-muted-foreground min-w-[3rem] text-center">
              {visiblePageIndex + 1} / {pageCount}
            </span>
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8 rounded-full"
              onClick={() => onNextPage()}
              disabled={!hasNextPage && visiblePageIndex >= pageCount - 1}
            >
              {isFetchingNextPage ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
