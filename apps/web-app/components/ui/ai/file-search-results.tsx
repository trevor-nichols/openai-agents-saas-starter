import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { FileSearchResult } from '@/lib/api/client/types.gen';

export type FileSearchResultsProps = {
  results: FileSearchResult[];
  className?: string;
};

const formatScore = (score?: number | null) => {
  if (score === null || score === undefined) return null;
  if (Number.isNaN(score)) return null;
  return score.toFixed(3);
};

const renderAttributes = (attributes?: Record<string, unknown> | null) => {
  if (!attributes || Object.keys(attributes).length === 0) return null;
  return (
    <dl className="grid gap-1 text-xs text-foreground/80">
      {Object.entries(attributes).map(([key, value]) => (
        <div key={key} className="flex items-start gap-2">
          <dt className="min-w-[80px] shrink-0 text-foreground/60">{key}</dt>
          <dd className="break-words text-foreground/80">{String(value)}</dd>
        </div>
      ))}
    </dl>
  );
};

export const FileSearchResults = ({ results, className }: FileSearchResultsProps) => {
  if (!results?.length) {
    return (
      <div className={cn('rounded-md border border-white/10 bg-muted/40 px-3 py-2 text-sm text-foreground/70', className)}>
        No files matched this search.
      </div>
    );
  }

  return (
    <div className={cn('space-y-2', className)}>
      {results.map((result) => (
        <div
          key={result.file_id}
          className="rounded-md border border-white/10 bg-muted/40 px-3 py-2 text-sm shadow-sm"
        >
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-medium">{result.filename ?? result.file_id}</span>
            {result.filename ? <span className="text-foreground/50">({result.file_id})</span> : null}
            {result.vector_store_id ? (
              <Badge variant="secondary" className="text-[11px]">
                VS: {result.vector_store_id}
              </Badge>
            ) : null}
            {formatScore(result.score) ? (
              <Badge variant="outline" className="text-[11px]">
                Score {formatScore(result.score)}
              </Badge>
            ) : null}
          </div>

          {result.text ? (
            <p className="mt-1 line-clamp-3 text-[13px] text-foreground/80">{result.text}</p>
          ) : null}

          {renderAttributes(result.attributes ?? undefined)}
        </div>
      ))}
    </div>
  );
};
