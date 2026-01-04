import 'server-only';

import {
  sendEmailVerificationApiV1AuthEmailSendPost,
  verifyEmailTokenApiV1AuthEmailVerifyPost,
} from '@/lib/api/client/sdk.gen';
import type {
  EmailVerificationSendSuccessResponse,
  EmailVerificationConfirmRequest,
  SuccessNoDataResponse,
} from '@/lib/api/client/types.gen';

import { getServerApiClient } from '../../apiClient';

export async function sendVerificationEmail(): Promise<EmailVerificationSendSuccessResponse> {
  const { client, auth } = await getServerApiClient();

  const response = await sendEmailVerificationApiV1AuthEmailSendPost({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
  });

  const payload = response.data;
  if (!payload) {
    throw new Error('Verification email send returned empty response.');
  }

  return payload;
}

export async function verifyEmailToken(
  payload: EmailVerificationConfirmRequest,
): Promise<SuccessNoDataResponse> {
  const { client, auth } = await getServerApiClient();

  const response = await verifyEmailTokenApiV1AuthEmailVerifyPost({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    headers: {
      'Content-Type': 'application/json',
    },
    body: payload,
  });

  const result = response.data;
  if (!result) {
    throw new Error('Email verification returned empty response.');
  }

  return result;
}
