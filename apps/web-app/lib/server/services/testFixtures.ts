'use server';

import {
  applyTestFixturesApiV1TestFixturesApplyPost,
  issueEmailVerificationTokenApiV1TestFixturesEmailVerificationTokenPost,
} from '@/lib/api/client/sdk.gen';
import type {
  EmailVerificationTokenRequest,
  EmailVerificationTokenResponse,
  FixtureApplyResult,
  PlaywrightFixtureSpec,
} from '@/lib/api/client/types.gen';
import { createApiClient } from '../apiClient';

export interface TestFixtureProxyResult {
  status: number;
  body: string;
  contentType: string;
  statusText?: string;
}

function resolveTextBody(error: unknown): string {
  if (!error) return '';
  if (typeof error === 'string') return error;
  try {
    return JSON.stringify(error);
  } catch {
    return '';
  }
}

type ApiFieldsResult<TData> =
  | {
      data: TData;
      error: undefined;
      response: Response;
    }
  | {
      data: undefined;
      error: unknown;
      response: Response;
    };

function toProxyResult(
  response: ApiFieldsResult<FixtureApplyResult | EmailVerificationTokenResponse>,
): TestFixtureProxyResult {
  const raw = response.data as string | FixtureApplyResult | EmailVerificationTokenResponse | undefined;
  const body = typeof raw === 'string'
    ? raw
    : resolveTextBody('error' in response ? response.error : raw);
  const contentType = response.response?.headers.get('content-type') ?? 'text/plain';

  return {
    status: response.response?.status ?? 502,
    body,
    contentType,
    statusText: response.response?.statusText,
  };
}

function resolveBodySerializer(payload: unknown) {
  if (typeof payload === 'string') {
    return (body: string) => body;
  }
  return undefined;
}

export async function applyTestFixtures(
  payload: PlaywrightFixtureSpec | string,
): Promise<TestFixtureProxyResult> {
  const client = createApiClient();
  const response = (await applyTestFixturesApiV1TestFixturesApplyPost({
    client,
    responseStyle: 'fields',
    throwOnError: false,
    parseAs: 'text',
    body: payload as PlaywrightFixtureSpec,
    bodySerializer: resolveBodySerializer(payload),
    cache: 'no-store',
  })) as ApiFieldsResult<FixtureApplyResult>;

  return toProxyResult(response);
}

export async function issueEmailVerificationToken(
  payload: EmailVerificationTokenRequest | string,
): Promise<TestFixtureProxyResult> {
  const client = createApiClient();
  const response = (await issueEmailVerificationTokenApiV1TestFixturesEmailVerificationTokenPost({
    client,
    responseStyle: 'fields',
    throwOnError: false,
    parseAs: 'text',
    body: payload as EmailVerificationTokenRequest,
    bodySerializer: resolveBodySerializer(payload),
    cache: 'no-store',
  })) as ApiFieldsResult<EmailVerificationTokenResponse>;

  return toProxyResult(response);
}
