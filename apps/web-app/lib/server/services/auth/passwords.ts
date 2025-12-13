'use server';

import {
  changePasswordApiV1AuthPasswordChangePost,
  confirmPasswordResetApiV1AuthPasswordConfirmPost,
  requestPasswordResetApiV1AuthPasswordForgotPost,
  adminResetPasswordApiV1AuthPasswordResetPost,
} from '@/lib/api/client/sdk.gen';
import type {
  PasswordChangeRequest,
  PasswordForgotRequest,
  PasswordResetConfirmRequest,
  PasswordResetRequest,
  SuccessNoDataResponse,
} from '@/lib/api/client/types.gen';

import { getServerApiClient } from '../../apiClient';

export async function requestPasswordReset(
  payload: PasswordForgotRequest,
): Promise<SuccessNoDataResponse> {
  const { client, auth } = await getServerApiClient();
  const response = await requestPasswordResetApiV1AuthPasswordForgotPost({
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
    throw new Error('Password reset request returned empty response.');
  }

  return result;
}

export async function confirmPasswordReset(
  payload: PasswordResetConfirmRequest,
): Promise<SuccessNoDataResponse> {
  const { client, auth } = await getServerApiClient();
  const response = await confirmPasswordResetApiV1AuthPasswordConfirmPost({
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
    throw new Error('Password reset confirmation returned empty response.');
  }

  return result;
}

export async function changePassword(
  payload: PasswordChangeRequest,
): Promise<SuccessNoDataResponse> {
  const { client, auth } = await getServerApiClient();
  const response = await changePasswordApiV1AuthPasswordChangePost({
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
    throw new Error('Password change returned empty response.');
  }

  return result;
}

export async function adminResetPassword(
  payload: PasswordResetRequest,
): Promise<SuccessNoDataResponse> {
  const { client, auth } = await getServerApiClient();
  const response = await adminResetPasswordApiV1AuthPasswordResetPost({
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
    throw new Error('Admin password reset returned empty response.');
  }

  return result;
}
