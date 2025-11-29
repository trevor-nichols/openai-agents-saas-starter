'use client';

import { ShieldAlert, ShieldCheck } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { GlassPanel } from '@/components/ui/foundation';
import { SkeletonPanel } from '@/components/ui/states';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import type { SignupAccessPolicy } from '@/types/signup';
import { resolveSignupPolicyMode, type SignupAccessPolicyMode } from '@/types/signup';

interface PolicyBannerProps {
  policy?: SignupAccessPolicy;
  isLoading?: boolean;
  error?: string;
  onRetry?: () => void;
}

const POLICY_LABELS: Record<SignupAccessPolicyMode, { label: string; description: string; tone: 'default' | 'secondary' | 'destructive' }> = {
  public: {
    label: 'Public signup',
    description: 'Anyone with the link can register instantly. Recommended only for dev and staging.',
    tone: 'destructive',
  },
  invite_only: {
    label: 'Invite only',
    description: 'Registration requires an invite token issued by operators.',
    tone: 'secondary',
  },
  approval: {
    label: 'Approval required',
    description: 'Prospects submit a request and ops issues invites after review.',
    tone: 'default',
  },
};

export function PolicyBanner({ policy, isLoading, error, onRetry }: PolicyBannerProps) {
  if (isLoading) {
    return <SkeletonPanel lines={3} className="rounded-2xl" />;
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <ShieldAlert className="h-4 w-4" aria-hidden="true" />
        <AlertTitle>Unable to load policy</AlertTitle>
        <AlertDescription className="flex items-center justify-between gap-3">
          <span>{error}</span>
          {onRetry ? (
            <Button size="sm" variant="outline" onClick={onRetry}>
              Retry
            </Button>
          ) : null}
        </AlertDescription>
      </Alert>
    );
  }

  if (!policy) {
    return null;
  }

  const mode = resolveSignupPolicyMode(policy);
  const copy = POLICY_LABELS[mode];
  const icon = mode === 'public' ? <ShieldAlert className="h-5 w-5 text-destructive" /> : <ShieldCheck className="h-5 w-5 text-primary" />;

  return (
    <GlassPanel className="flex items-center gap-4">
      {icon}
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <Badge variant="outline">{copy.label}</Badge>
          <span className="text-xs uppercase tracking-[0.3em] text-foreground/50">Signup policy</span>
        </div>
        <p className="text-sm text-foreground/70">{copy.description}</p>
      </div>
    </GlassPanel>
  );
}
