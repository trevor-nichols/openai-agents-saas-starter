import type {
  GuardrailDetail as BackendGuardrailDetail,
  GuardrailSummary as BackendGuardrailSummary,
  PresetDetail as BackendPresetDetail,
  PresetSummary as BackendPresetSummary,
} from '@/lib/api/client/types.gen';

export type GuardrailSummary = BackendGuardrailSummary;
export type GuardrailDetail = BackendGuardrailDetail;

export type PresetSummary = BackendPresetSummary;
export type PresetDetail = BackendPresetDetail;
