/**
 * Thin helpers around the fixture-only backend endpoints.
 * Intended for Playwright seeds and local deterministic setup.
 * These should not be wired into production UI flows.
 */

import {
  applyTestFixturesApiV1TestFixturesApplyPost,
  issueEmailVerificationTokenApiV1TestFixturesEmailVerificationTokenPost,
} from '@/lib/api/client/sdk.gen';
import type {
  ApplyTestFixturesApiV1TestFixturesApplyPostResponses,
  EmailVerificationTokenRequest,
  EmailVerificationTokenResponse,
  PlaywrightFixtureSpec,
} from '@/lib/api/client/types.gen';

type ClientOptions = { baseUrl?: string };

/**
 * Apply a test fixture spec (Playwright/local dev).
 * Accepts the raw PlaywrightFixtureSpec and forwards it directly as the request body.
 */
export async function applyTestFixtures(
  spec: PlaywrightFixtureSpec,
  options?: ClientOptions,
): Promise<ApplyTestFixturesApiV1TestFixturesApplyPostResponses['201']> {
  const clientOptions = options?.baseUrl ? { baseUrl: options.baseUrl } : {};
  const response = await applyTestFixturesApiV1TestFixturesApplyPost({
    body: spec,
    responseStyle: 'fields',
    ...clientOptions,
  });
  if (!response.data) {
    throw new Error('Fixture apply returned empty response.');
  }
  return response.data;
}

/**
 * Issue an email verification token via the fixture-only endpoint.
 */
export async function issueEmailVerificationToken(
  request: EmailVerificationTokenRequest,
  options?: ClientOptions,
): Promise<EmailVerificationTokenResponse> {
  const clientOptions = options?.baseUrl ? { baseUrl: options.baseUrl } : {};
  const response = await issueEmailVerificationTokenApiV1TestFixturesEmailVerificationTokenPost({
    body: request,
    responseStyle: 'fields',
    ...clientOptions,
  });
  if (!response.data) {
    throw new Error('Email verification token response was empty.');
  }
  return response.data;
}
