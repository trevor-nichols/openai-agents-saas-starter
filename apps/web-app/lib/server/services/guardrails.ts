import 'server-only';

import {
  getGuardrailApiV1GuardrailsGuardrailKeyGet,
  getPresetApiV1GuardrailsPresetsPresetKeyGet,
  listGuardrailsApiV1GuardrailsGet,
  listPresetsApiV1GuardrailsPresetsGet,
} from '@/lib/api/client/sdk.gen';
import type {
  GuardrailDetail,
  GuardrailSummary,
  PresetDetail,
  PresetSummary,
} from '@/lib/api/client/types.gen';

import { getServerApiClient } from '../apiClient';

export async function listGuardrails(): Promise<GuardrailSummary[]> {
  const { client, auth } = await getServerApiClient();
  const response = await listGuardrailsApiV1GuardrailsGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
  });

  return response.data ?? [];
}

export async function listGuardrailPresets(): Promise<PresetSummary[]> {
  const { client, auth } = await getServerApiClient();
  const response = await listPresetsApiV1GuardrailsPresetsGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
  });

  return response.data ?? [];
}

export async function getGuardrail(guardrailKey: string): Promise<GuardrailDetail> {
  if (!guardrailKey) {
    throw new Error('Guardrail key is required.');
  }

  const { client, auth } = await getServerApiClient();
  const response = await getGuardrailApiV1GuardrailsGuardrailKeyGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    path: {
      guardrail_key: guardrailKey,
    },
  });

  if (!response.data) {
    throw new Error('Guardrail not found.');
  }

  return response.data;
}

export async function getGuardrailPreset(presetKey: string): Promise<PresetDetail> {
  if (!presetKey) {
    throw new Error('Preset key is required.');
  }

  const { client, auth } = await getServerApiClient();
  const response = await getPresetApiV1GuardrailsPresetsPresetKeyGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    path: {
      preset_key: presetKey,
    },
  });

  if (!response.data) {
    throw new Error('Preset not found.');
  }

  return response.data;
}
