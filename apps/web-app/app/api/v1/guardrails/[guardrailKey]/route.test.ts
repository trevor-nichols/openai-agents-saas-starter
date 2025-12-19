import { vi } from 'vitest';

import type { GuardrailDetail } from '@/types/guardrails';

import { GET } from './route';

const getGuardrail = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/guardrails', () => ({
  getGuardrail,
}));

const buildContext = (guardrailKey?: string) => ({
  params: Promise.resolve({ guardrailKey }),
});

describe('/api/v1/guardrails/[guardrailKey] route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns 400 when guardrailKey is missing', async () => {
    const response = await GET({} as Request, buildContext());

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'Guardrail key is required.',
    });
    expect(getGuardrail).not.toHaveBeenCalled();
  });

  it('returns guardrail details on success', async () => {
    const guardrail: GuardrailDetail = {
      key: 'pii_input',
      display_name: 'PII Input',
      description: 'Checks input for PII',
      stage: 'input',
      engine: 'llm',
      supports_masking: true,
      uses_conversation_history: false,
      tripwire_on_error: false,
      default_config: {},
      config_schema: {},
    };
    getGuardrail.mockResolvedValueOnce(guardrail);

    const response = await GET({} as Request, buildContext('pii_input'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({
      success: true,
      guardrail,
    });
  });

  it('maps missing token errors to 401', async () => {
    getGuardrail.mockRejectedValueOnce(new Error('Missing access token'));

    const response = await GET({} as Request, buildContext('pii_input'));

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'Missing access token',
    });
  });

  it('maps not found errors to 404', async () => {
    getGuardrail.mockRejectedValueOnce(new Error('not found'));

    const response = await GET({} as Request, buildContext('pii_input'));

    expect(response.status).toBe(404);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'not found',
    });
  });
});
