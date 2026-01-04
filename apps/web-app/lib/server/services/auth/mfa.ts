import 'server-only';

import {
  completeMfaChallengeApiV1AuthMfaCompletePost,
  listMfaMethodsApiV1AuthMfaGet,
  regenerateRecoveryCodesApiV1AuthMfaRecoveryRegeneratePost,
  revokeMfaMethodApiV1AuthMfaMethodIdDelete,
  startTotpEnrollmentApiV1AuthMfaTotpEnrollPost,
  verifyTotpApiV1AuthMfaTotpVerifyPost,
} from '@/lib/api/client/sdk.gen';
import type {
  MfaChallengeCompleteRequest,
  MfaMethodView,
  RecoveryCodesResponse,
  SuccessNoDataResponse,
  TotpEnrollResponse,
  TotpVerifyRequest,
  UserSessionResponse,
} from '@/lib/api/client/types.gen';
import { createApiClient, getServerApiClient } from '../../apiClient';

export async function listMfaMethods(): Promise<MfaMethodView[]> {
  const { client, auth } = await getServerApiClient();
  const response = await listMfaMethodsApiV1AuthMfaGet({
    client,
    auth,
    throwOnError: true,
    responseStyle: 'fields',
  });

  return response.data ?? [];
}

export async function startTotpEnrollment(options?: {
  label?: string | null;
}): Promise<TotpEnrollResponse> {
  const { client, auth } = await getServerApiClient();
  const response = await startTotpEnrollmentApiV1AuthMfaTotpEnrollPost({
    client,
    auth,
    throwOnError: true,
    responseStyle: 'fields',
    query: options?.label ? { label: options.label } : undefined,
  });

  if (!response.data) {
    throw new Error('TOTP enrollment response missing data.');
  }

  return response.data;
}

export async function verifyTotp(payload: TotpVerifyRequest): Promise<SuccessNoDataResponse> {
  const { client, auth } = await getServerApiClient();
  const response = await verifyTotpApiV1AuthMfaTotpVerifyPost({
    client,
    auth,
    throwOnError: true,
    responseStyle: 'fields',
    body: payload,
  });

  return response.data ?? { success: true, message: 'TOTP verified', data: null };
}

export async function completeMfaChallenge(
  payload: MfaChallengeCompleteRequest,
): Promise<UserSessionResponse> {
  const response = await completeMfaChallengeApiV1AuthMfaCompletePost({
    client: createApiClient(),
    throwOnError: true,
    responseStyle: 'fields',
    body: payload,
  });

  if (!response.data) {
    throw new Error('MFA completion response missing data.');
  }

  return response.data;
}

export async function regenerateRecoveryCodes(): Promise<RecoveryCodesResponse> {
  const { client, auth } = await getServerApiClient();
  const response = await regenerateRecoveryCodesApiV1AuthMfaRecoveryRegeneratePost({
    client,
    auth,
    throwOnError: true,
    responseStyle: 'fields',
  });

  if (!response.data) {
    throw new Error('Recovery code response missing data.');
  }

  return response.data;
}

export async function revokeMfaMethod(methodId: string): Promise<SuccessNoDataResponse> {
  if (!methodId) {
    throw new Error('methodId is required.');
  }

  const { client, auth } = await getServerApiClient();
  const response = await revokeMfaMethodApiV1AuthMfaMethodIdDelete({
    client,
    auth,
    throwOnError: true,
    responseStyle: 'fields',
    path: { method_id: methodId },
  });

  return response.data ?? { success: true, message: 'MFA method revoked', data: null };
}
