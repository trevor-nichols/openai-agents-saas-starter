'use client';

import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { InlineTag } from '@/components/ui/foundation';

import { SUCCESS_COPY } from '../constants';
import type { AccessRequestSubmission } from '../types';

interface SubmissionSuccessProps {
  submission: AccessRequestSubmission;
  onReset?: () => void;
}

export function SubmissionSuccess({ submission, onReset }: SubmissionSuccessProps) {
  const copy = SUCCESS_COPY[submission.policy];

  return (
    <div className="space-y-6 text-center">
      <div className="space-y-2">
        <InlineTag tone="positive">Access request received</InlineTag>
        <h2 className="text-2xl font-semibold tracking-tight">{copy.title}</h2>
        <p className="text-sm text-foreground/70">
          We sent a confirmation to <span className="font-medium text-foreground">{submission.email}</span>.
          {submission.policy === 'public'
            ? ' You can still create an account immediately while we review your note.'
            : ''}
        </p>
      </div>
      <p className="text-base text-foreground/80">{copy.body}</p>
      <div className="flex flex-wrap justify-center gap-3">
        {submission.policy === 'public' ? (
          <Button asChild>
            <Link href="/register">Create an account</Link>
          </Button>
        ) : null}
        <Button variant="outline" onClick={onReset}>
          Submit another request
        </Button>
      </div>
    </div>
  );
}
