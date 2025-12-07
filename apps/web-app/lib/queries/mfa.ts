import { useMutation, useQuery } from '@tanstack/react-query';

import {
  completeMfaChallengeRequest,
  listMfaMethodsRequest,
  regenerateRecoveryCodesRequest,
  revokeMfaMethodRequest,
  startTotpEnrollmentRequest,
  verifyTotpRequest,
} from '@/lib/api/mfa';
import type {
  MfaChallengeCompleteRequest,
  TotpVerifyRequest,
} from '@/lib/api/client/types.gen';

export function useMfaMethodsQuery(enabled = true) {
  return useQuery({
    queryKey: ['mfa-methods'],
    queryFn: () => listMfaMethodsRequest(),
    enabled,
  });
}

export function useStartTotpEnrollmentMutation() {
  return useMutation({
    mutationFn: (label?: string | null) => startTotpEnrollmentRequest(label),
  });
}

export function useVerifyTotpMutation() {
  return useMutation({
    mutationFn: (payload: TotpVerifyRequest) => verifyTotpRequest(payload),
  });
}

export function useRevokeMfaMethodMutation() {
  return useMutation({
    mutationFn: (methodId: string) => revokeMfaMethodRequest(methodId),
  });
}

export function useRegenerateRecoveryCodesMutation() {
  return useMutation({
    mutationFn: () => regenerateRecoveryCodesRequest(),
  });
}

export function useCompleteMfaChallengeMutation() {
  return useMutation({
    mutationFn: (payload: MfaChallengeCompleteRequest) => completeMfaChallengeRequest(payload),
  });
}
