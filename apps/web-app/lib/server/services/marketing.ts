'use server';

import { submitContactApiV1ContactPost } from '@/lib/api/client/sdk.gen';
import type { ContactSubmissionRequest } from '@/lib/api/client/types.gen';
import { createApiClient } from '../apiClient';
import type { ContactSubmission } from '@/types/marketing';

import { MarketingServiceError } from './marketing.errors';

export async function submitContact(payload: ContactSubmission): Promise<void> {
  const client = createApiClient();

  const body = mapSubmissionToRequest(payload);

  try {
    await submitContactApiV1ContactPost({
      client,
      responseStyle: 'fields',
      throwOnError: true,
      headers: {
        'Content-Type': 'application/json',
      },
      body,
    });
  } catch (error) {
    throw normalizeError(error, 'Unable to submit contact request.');
  }
}

function mapSubmissionToRequest(submission: ContactSubmission): ContactSubmissionRequest {
  return {
    name: normalize(submission.name),
    email: submission.email.trim(),
    company: normalize(submission.company),
    topic: normalize(submission.topic),
    message: submission.message.trim(),
    honeypot: normalize(submission.honeypot),
  } satisfies ContactSubmissionRequest;
}

function normalize(value: string | null | undefined): string | null {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function normalizeError(error: unknown, fallbackMessage: string): MarketingServiceError {
  if (error instanceof MarketingServiceError) {
    return error;
  }

  const message = error instanceof Error ? error.message : fallbackMessage;
  const status = mapErrorToStatus(message);
  return new MarketingServiceError(message || fallbackMessage, status);
}

function mapErrorToStatus(message: string): number {
  const normalized = (message ?? '').toLowerCase();
  if (normalized.includes('missing access token')) return 401;
  if (normalized.includes('forbidden') || normalized.includes('permission')) return 403;
  if (normalized.includes('not found')) return 404;
  if (normalized.includes('validation')) return 422;
  return 500;
}
