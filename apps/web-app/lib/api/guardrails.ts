import type { GuardrailDetail, GuardrailSummary, PresetDetail, PresetSummary } from '@/types/guardrails';
import { apiV1Path } from '@/lib/apiPaths';

interface GuardrailListResponse {
  success: boolean;
  guardrails?: GuardrailSummary[];
  error?: string;
}

interface GuardrailDetailResponse {
  success: boolean;
  guardrail?: GuardrailDetail;
  error?: string;
}

interface PresetListResponse {
  success: boolean;
  presets?: PresetSummary[];
  error?: string;
}

interface PresetDetailResponse {
  success: boolean;
  preset?: PresetDetail;
  error?: string;
}

export async function fetchGuardrails(): Promise<GuardrailSummary[]> {
  const response = await fetch(apiV1Path('/guardrails'), { cache: 'no-store' });
  const payload = (await response.json().catch(() => ({}))) as GuardrailListResponse;

  if (!response.ok) {
    throw new Error(payload.error || 'Failed to load guardrails');
  }

  if (!payload.success || !payload.guardrails) {
    throw new Error(payload.error || 'No guardrails returned from API');
  }

  return payload.guardrails;
}

export async function fetchGuardrail(guardrailKey: string): Promise<GuardrailDetail> {
  const response = await fetch(apiV1Path(`/guardrails/${encodeURIComponent(guardrailKey)}`), {
    cache: 'no-store',
  });
  const payload = (await response.json().catch(() => ({}))) as GuardrailDetailResponse;

  if (!response.ok) {
    throw new Error(payload.error || 'Failed to load guardrail');
  }

  if (!payload.success || !payload.guardrail) {
    throw new Error(payload.error || 'Guardrail not found');
  }

  return payload.guardrail;
}

export async function fetchGuardrailPresets(): Promise<PresetSummary[]> {
  const response = await fetch(apiV1Path('/guardrails/presets'), { cache: 'no-store' });
  const payload = (await response.json().catch(() => ({}))) as PresetListResponse;

  if (!response.ok) {
    throw new Error(payload.error || 'Failed to load guardrail presets');
  }

  if (!payload.success || !payload.presets) {
    throw new Error(payload.error || 'No guardrail presets returned from API');
  }

  return payload.presets;
}

export async function fetchGuardrailPreset(presetKey: string): Promise<PresetDetail> {
  const response = await fetch(apiV1Path(`/guardrails/presets/${encodeURIComponent(presetKey)}`), {
    cache: 'no-store',
  });
  const payload = (await response.json().catch(() => ({}))) as PresetDetailResponse;

  if (!response.ok) {
    throw new Error(payload.error || 'Failed to load guardrail preset');
  }

  if (!payload.success || !payload.preset) {
    throw new Error(payload.error || 'Guardrail preset not found');
  }

  return payload.preset;
}
