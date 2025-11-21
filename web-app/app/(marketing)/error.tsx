'use client';

import Link from 'next/link';
import { useEffect } from 'react';

import { Button } from '@/components/ui/button';
import { ErrorState } from '@/components/ui/states/ErrorState';

interface MarketingErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function MarketingError({ error, reset }: MarketingErrorProps) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="mx-auto w-full max-w-2xl py-24">
      <ErrorState
        title="We hit a snag"
        message={error?.message ?? 'This marketing page failed to render. Refresh to try again or jump back to safety.'}
        action={
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Button onClick={reset}>Refresh section</Button>
            <Button variant="outline" asChild>
              <Link href="/">Go to homepage</Link>
            </Button>
          </div>
        }
      />
    </div>
  );
}
