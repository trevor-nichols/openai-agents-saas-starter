'use client';

import Link from 'next/link';
import { useEffect } from 'react';

import { Button } from '@/components/ui/button';
import { ErrorState } from '@/components/ui/states/ErrorState';

interface AppRouteErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function AppRouteError({ error, reset }: AppRouteErrorProps) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="mx-auto w-full max-w-3xl py-16">
      <ErrorState
        title="Workspace failed to load"
        message={error?.message ?? 'Something went sideways while rendering this workspace view.'}
        action={
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Button onClick={reset}>Try again</Button>
            <Button variant="outline" asChild>
              <Link href="/status">Check platform status</Link>
            </Button>
          </div>
        }
      />
    </div>
  );
}
