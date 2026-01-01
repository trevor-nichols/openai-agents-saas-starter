'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useMemo, useRef, useState } from 'react';

import { MfaChallengeDialog } from '@/components/auth/MfaChallengeDialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Spinner } from '@/components/ui/spinner';
import type { MfaChallengeResponse } from '@/lib/api/client/types.gen';
import { resolveSafeRedirect } from '@/lib/auth/sso';
import { useCompleteSsoMutation } from '@/lib/queries/sso';

type CallbackState = 'loading' | 'mfa' | 'error';

interface SsoCallbackClientProps {
  provider: string;
  code?: string | null;
  state?: string | null;
  error?: string | null;
  errorDescription?: string | null;
}

export function SsoCallbackClient({
  provider,
  code,
  state,
  error,
  errorDescription,
}: SsoCallbackClientProps) {
  const router = useRouter();
  const [status, setStatus] = useState<CallbackState>('loading');
  const [runtimeMessage, setRuntimeMessage] = useState<string | null>(null);
  const [redirectTo, setRedirectTo] = useState<string>('/dashboard');
  const [mfaChallenge, setMfaChallenge] = useState<MfaChallengeResponse | null>(null);
  const startedRef = useRef(false);
  const mutation = useCompleteSsoMutation();

  const preflightMessage = useMemo(() => {
    if (error) {
      return errorDescription ?? `The identity provider returned "${error}".`;
    }
    if (!code || !state) {
      return 'Missing authorization code or state. Please restart sign-in.';
    }
    return null;
  }, [code, error, errorDescription, state]);

  useEffect(() => {
    if (startedRef.current) {
      return;
    }
    if (preflightMessage) {
      return;
    }
    startedRef.current = true;

    if (!code || !state) {
      return;
    }

    mutation
      .mutateAsync({ provider, code, state })
      .then((result) => {
        const safeRedirect = resolveSafeRedirect(result.redirect_to) ?? '/dashboard';
        setRedirectTo(safeRedirect);

        if (result.status === 'mfa_required') {
          setStatus('mfa');
          setMfaChallenge(result.mfa);
          return;
        }

        router.push(safeRedirect);
        router.refresh();
      })
      .catch((err) => {
        setStatus('error');
        setRuntimeMessage(err instanceof Error ? err.message : 'Unable to complete sign-in.');
      });
  }, [code, mutation, preflightMessage, provider, router, state]);

  const message = preflightMessage ?? runtimeMessage;
  const effectiveStatus: CallbackState = preflightMessage ? 'error' : status;

  const badge = (() => {
    switch (effectiveStatus) {
      case 'mfa':
        return (
          <Badge variant="secondary" className="gap-2 bg-amber-500/15 text-amber-100">
            MFA required
          </Badge>
        );
      case 'error':
        return (
          <Badge variant="destructive" className="gap-2">
            Sign-in failed
          </Badge>
        );
      case 'loading':
      default:
        return (
          <Badge variant="outline" className="gap-2 border-blue-400/60 text-blue-100">
            Completing sign-in…
          </Badge>
        );
    }
  })();

  return (
    <>
      <div className="space-y-6 text-sm text-muted-foreground">
        <div className="space-y-2">
          {badge}
          <p>
            {effectiveStatus === 'mfa'
              ? 'Your account requires an additional verification step.'
              : 'We are finalizing your SSO session.'}
          </p>
        </div>

        {effectiveStatus === 'loading' ? (
          <div className="flex items-center gap-2">
            <Spinner className="h-4 w-4" />
            Redirecting after verification…
          </div>
        ) : null}

        {effectiveStatus === 'error' && message ? (
          <p className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-destructive">
            {message}
          </p>
        ) : null}

        {effectiveStatus === 'error' ? (
          <Button asChild className="w-full">
            <Link href="/login">Return to sign in</Link>
          </Button>
        ) : null}
      </div>

      <MfaChallengeDialog
        open={Boolean(mfaChallenge)}
        challenge={mfaChallenge}
        onClose={() => setMfaChallenge(null)}
        onSuccess={() => {
          setMfaChallenge(null);
          router.push(redirectTo);
          router.refresh();
        }}
      />
    </>
  );
}
