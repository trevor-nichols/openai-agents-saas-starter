import { useQuery } from '@tanstack/react-query';

import {
  fetchGuardrail,
  fetchGuardrailPreset,
  fetchGuardrailPresets,
  fetchGuardrails,
} from '@/lib/api/guardrails';

import { queryKeys } from './keys';

export function useGuardrails() {
  const {
    data: guardrails = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: queryKeys.guardrails.list(),
    queryFn: fetchGuardrails,
    staleTime: 30 * 1000,
  });

  return {
    guardrails,
    isLoadingGuardrails: isLoading,
    guardrailsError: error instanceof Error ? error : null,
  };
}

export function useGuardrail(guardrailKey: string | null) {
  const enabled = Boolean(guardrailKey);
  const {
    data,
    isLoading,
    error,
  } = useQuery({
    queryKey: guardrailKey
      ? queryKeys.guardrails.detail(guardrailKey)
      : queryKeys.guardrails.detail(''),
    queryFn: () => fetchGuardrail(guardrailKey as string),
    enabled,
    staleTime: 30 * 1000,
  });

  return {
    guardrail: data ?? null,
    isLoadingGuardrail: isLoading && enabled,
    guardrailError: error instanceof Error ? error : null,
  };
}

export function useGuardrailPresets() {
  const {
    data: presets = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: queryKeys.guardrails.presets.list(),
    queryFn: fetchGuardrailPresets,
    staleTime: 30 * 1000,
  });

  return {
    guardrailPresets: presets,
    isLoadingGuardrailPresets: isLoading,
    guardrailPresetsError: error instanceof Error ? error : null,
  };
}

export function useGuardrailPreset(presetKey: string | null) {
  const enabled = Boolean(presetKey);
  const {
    data,
    isLoading,
    error,
  } = useQuery({
    queryKey: presetKey
      ? queryKeys.guardrails.presets.detail(presetKey)
      : queryKeys.guardrails.presets.detail(''),
    queryFn: () => fetchGuardrailPreset(presetKey as string),
    enabled,
    staleTime: 30 * 1000,
  });

  return {
    guardrailPreset: data ?? null,
    isLoadingGuardrailPreset: isLoading && enabled,
    guardrailPresetError: error instanceof Error ? error : null,
  };
}
