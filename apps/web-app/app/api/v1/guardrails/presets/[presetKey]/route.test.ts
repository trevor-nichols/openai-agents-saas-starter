import { vi } from 'vitest';

import type { PresetDetail } from '@/types/guardrails';

import { GET } from './route';

const getGuardrailPreset = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/guardrails', () => ({
  getGuardrailPreset,
}));

const buildContext = (presetKey?: string) => ({
  params: Promise.resolve({ presetKey }),
});

describe('/api/v1/guardrails/presets/[presetKey] route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns 400 when presetKey is missing', async () => {
    const response = await GET({} as Request, buildContext());

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'Preset key is required.',
    });
    expect(getGuardrailPreset).not.toHaveBeenCalled();
  });

  it('returns preset detail on success', async () => {
    const preset: PresetDetail = {
      key: 'default_safety',
      display_name: 'Default Safety',
      description: 'Baseline safety bundle',
      guardrail_count: 3,
      guardrails: [],
    };
    getGuardrailPreset.mockResolvedValueOnce(preset);

    const response = await GET({} as Request, buildContext('default_safety'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({
      success: true,
      preset,
    });
  });

  it('maps missing token errors to 401', async () => {
    getGuardrailPreset.mockRejectedValueOnce(new Error('Missing access token'));

    const response = await GET({} as Request, buildContext('default_safety'));

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'Missing access token',
    });
  });

  it('maps not found errors to 404', async () => {
    getGuardrailPreset.mockRejectedValueOnce(new Error('Not found'));

    const response = await GET({} as Request, buildContext('default_safety'));

    expect(response.status).toBe(404);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'Not found',
    });
  });
});
