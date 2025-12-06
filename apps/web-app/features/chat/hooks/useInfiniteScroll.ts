import { useCallback, useEffect, useRef } from 'react';

type LoadMoreFn = () => void;

interface UseInfiniteScrollOptions {
  loadMore?: LoadMoreFn;
  hasNextPage?: boolean;
  isLoading?: boolean;
  rootMargin?: string;
}

/**
 * IntersectionObserver-based infinite scroll sentinel.
 */
export function useInfiniteScroll({
  loadMore,
  hasNextPage,
  isLoading,
  rootMargin = '20px',
}: UseInfiniteScrollOptions) {
  const observerRef = useRef<HTMLDivElement>(null);

  const handleObserver = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      const [target] = entries;
      if (target?.isIntersecting && hasNextPage && !isLoading && loadMore) {
        loadMore();
      }
    },
    [loadMore, hasNextPage, isLoading],
  );

  useEffect(() => {
    const element = observerRef.current;
    if (!element) return undefined;

    const observer = new IntersectionObserver(handleObserver, {
      root: null,
      rootMargin,
      threshold: 0,
    });

    observer.observe(element);
    return () => observer.disconnect();
  }, [handleObserver, rootMargin]);

  return observerRef;
}
