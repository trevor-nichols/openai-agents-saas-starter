'use client';

import { ChevronRight, Database, Loader2, Trash2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import { cn } from '@/lib/utils';
import type { VectorStoreListResponse } from '@/lib/api/client/types.gen';

interface VectorStoreListProps {
  items: VectorStoreListResponse['items'];
  selectedId: string | null;
  isLoading: boolean;
  isError: boolean;
  errorMessage?: string;
  isDeleting: boolean;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}

export function VectorStoreList({
  items,
  selectedId,
  isLoading,
  isError,
  errorMessage,
  isDeleting,
  onSelect,
  onDelete,
}: VectorStoreListProps) {
  if (isLoading) {
    return <SkeletonPanel lines={6} />;
  }

  if (isError) {
    return <ErrorState title="Failed to load vector stores" message={errorMessage} />;
  }

  if (!items.length) {
    return <EmptyState title="No vector stores" description="Create a store to attach files." />;
  }

  return (
    <div className="space-y-2">
      {items.map((vs) => {
        const isSelected = selectedId === vs.id;
        return (
          <div
            key={vs.id}
            onClick={() => onSelect(vs.id)}
            className={cn(
              "group relative flex items-center justify-between gap-3 rounded-lg border p-3 transition-all cursor-pointer",
              isSelected 
                ? "border-primary/50 bg-primary/5 shadow-sm" 
                : "border-border/50 bg-card hover:border-border/80 hover:bg-accent/50"
            )}
          >
            <div className="flex items-center gap-3 min-w-0">
              <div className={cn(
                "flex h-9 w-9 items-center justify-center rounded-full border transition-colors",
                isSelected ? "bg-primary/10 border-primary/20 text-primary" : "bg-muted border-border text-muted-foreground"
              )}>
                <Database className="h-4 w-4" />
              </div>
              <div className="min-w-0">
                <div className={cn("font-medium truncate", isSelected ? "text-primary" : "text-foreground")}>
                  {vs.name}
                </div>
                <div className="text-[10px] text-muted-foreground font-mono truncate max-w-[180px]">
                  {vs.id}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-1">
               <Button
                size="icon"
                variant="ghost"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(vs.id);
                }}
                disabled={isDeleting}
                className="h-8 w-8 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity focus:opacity-100"
                title="Delete Store"
              >
                {isDeleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
              </Button>
              {isSelected && (
                 <ChevronRight className="h-4 w-4 text-primary animate-in slide-in-from-left-1" />
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
