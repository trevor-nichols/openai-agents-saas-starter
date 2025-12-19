import { vi } from 'vitest';

import type { PresetSummary } from '@/types/guardrails';

import { GET } from './route';

const listGuardrailPresets = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/guardrails', () => ({
  listGuardrailPresets,
}));

describe('/api/v1/guardrails/presets route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns guardrail presets on success', async () => {
    const presets: PresetSummary[] = [
      {
        key: 'default_safety',
        display_name: 'Default Safety',
        description: 'Baseline safety bundle',
        guardrail_count: 3,
      },
    ];
    listGuardrailPresets.mockResolvedValueOnce(presets);

    const response = await GET();

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({
      success: true,
      presets,
    });
    expect(listGuardrailPresets).toHaveBeenCalledTimes(1);
  });

  it('maps missing token errors to 401', async () => {
    listGuardrailPresets.mockRejectedValueOnce(new Error('Missing access token'));

    const response = await GET();

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'Missing access token',
    });
  });

  it('maps unknown errors to 500', async () => {
    listGuardrailPresets.mockRejectedValueOnce(new Error('boom'));

    const response = await GET();

    expect(response.status).toBe(500);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'boom',
    });
  });
});
