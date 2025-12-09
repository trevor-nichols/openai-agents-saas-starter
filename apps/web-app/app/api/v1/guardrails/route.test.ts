import { vi } from 'vitest';

import type { GuardrailSummary } from '@/types/guardrails';

import { GET } from './route';

const listGuardrails = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/guardrails', () => ({
  listGuardrails,
}));

describe('/api/v1/guardrails route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns guardrails on success', async () => {
    const guardrails: GuardrailSummary[] = [
      {
        key: 'pii_input',
        display_name: 'PII Input',
        description: 'Checks input for PII',
        stage: 'input',
        engine: 'llm',
        supports_masking: true,
      },
    ];
    listGuardrails.mockResolvedValueOnce(guardrails);

    const response = await GET();

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({
      success: true,
      guardrails,
    });
    expect(listGuardrails).toHaveBeenCalledTimes(1);
  });

  it('maps missing token errors to 401', async () => {
    listGuardrails.mockRejectedValueOnce(new Error('Missing access token'));

    const response = await GET();

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'Missing access token',
    });
  });

  it('maps unknown errors to 500', async () => {
    listGuardrails.mockRejectedValueOnce(new Error('boom'));

    const response = await GET();

    expect(response.status).toBe(500);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'boom',
    });
  });
});
