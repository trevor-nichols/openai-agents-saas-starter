'use client';

import { ErrorState } from '@/components/ui/states/ErrorState';

interface AuthErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function AuthError({ error, reset }: AuthErrorProps) {
  return (
    <div className="mx-auto w-full max-w-md">
      <ErrorState
        title="Authentication route error"
        message={error?.message ?? 'Something went wrong while loading this flow.'}
        onRetry={reset}
      />
    </div>
  );
}
