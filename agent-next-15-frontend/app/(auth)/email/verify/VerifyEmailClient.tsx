'use client';

import { useCallback, useEffect, useState } from 'react';
import { Loader2, MailCheck, MailQuestion } from 'lucide-react';

import { sendVerificationEmailAction, verifyEmailTokenAction } from '@/app/actions/auth/email';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';

interface VerifyEmailClientProps {
  token?: string;
}

type VerifyState = 'idle' | 'verifying' | 'verified' | 'error';

export function VerifyEmailClient({ token }: VerifyEmailClientProps) {
  const [state, setState] = useState<VerifyState>(token ? 'verifying' : 'idle');
  const [message, setMessage] = useState<string>('');
  const [isResending, setIsResending] = useState(false);
  const { success, error } = useToast();

  const handleVerify = useCallback(async () => {
    if (!token) return;
    setState('verifying');
    try {
      await verifyEmailTokenAction({ token });
      setState('verified');
      setMessage('Your email address is verified.');
      success({
        title: 'Email verified',
        description: 'Thanks for confirming your inbox.',
      });
    } catch (err) {
      setState('error');
      setMessage(err instanceof Error ? err.message : 'The verification link is invalid or expired.');
      error({
        title: 'Verification failed',
        description: err instanceof Error ? err.message : 'Try requesting another link.',
      });
    }
  }, [token, success, error]);

  useEffect(() => {
    if (token) {
      void handleVerify();
    }
  }, [token, handleVerify]);

  const handleResend = async () => {
    setIsResending(true);
    try {
      await sendVerificationEmailAction();
      success({
        title: 'Verification email sent',
        description: 'Check your inbox for the latest link.',
      });
    } catch (err) {
      error({
        title: 'Unable to resend',
        description: err instanceof Error ? err.message : 'Please try again in a moment.',
      });
    } finally {
      setIsResending(false);
    }
  };

  const renderStatus = () => {
    switch (state) {
      case 'verifying':
        return (
          <Badge variant="outline" className="gap-2 border-blue-400 text-blue-100">
            <Loader2 className="h-3.5 w-3.5 animate-spin" /> Verifying…
          </Badge>
        );
      case 'verified':
        return (
          <Badge variant="secondary" className="gap-2 bg-emerald-500/20 text-emerald-100">
            <MailCheck className="h-3.5 w-3.5" /> Verified
          </Badge>
        );
      case 'error':
        return (
          <Badge variant="destructive" className="gap-2">
            <MailQuestion className="h-3.5 w-3.5" /> Needs attention
          </Badge>
        );
      case 'idle':
      default:
        return <Badge variant="secondary">Pending verification</Badge>;
    }
  };

  return (
    <div className="space-y-6 text-sm text-muted-foreground">
      <div className="space-y-2">
        <div>{renderStatus()}</div>
        <p>
          We sent a verification link to your inbox when you registered. Click the button below if you need us to resend
          it, or paste the link again to trigger verification automatically.
        </p>
      </div>

      {state === 'error' && message ? (
        <p className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-destructive">{message}</p>
      ) : null}

      {token ? (
        <Button type="button" variant="secondary" onClick={handleVerify} disabled={state === 'verifying'}>
          {state === 'verifying' ? 'Verifying token...' : 'Verify this token again'}
        </Button>
      ) : (
        <p className="text-xs text-muted-foreground">
          Add <code>?token=YOUR_TOKEN</code> to the URL if you need to paste the link manually.
        </p>
      )}

      <Button type="button" className="w-full" onClick={handleResend} disabled={isResending}>
        {isResending ? 'Sending...' : 'Resend verification email'}
      </Button>
    </div>
  );
}
