import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';

import { MfaChallengeDialog } from '@/components/auth/MfaChallengeDialog';

const completeMutation = vi.hoisted(() => vi.fn());

vi.mock('@/lib/queries/mfa', () => ({
  useCompleteMfaChallengeMutation: () => ({ mutateAsync: completeMutation, isPending: false }),
}));

const challenge = {
  mfa_required: true,
  challenge_token: 'token',
  methods: [
    { id: 'm1', method_type: 'totp', label: 'Primary', verified_at: null, last_used_at: null, revoked_at: null },
    { id: 'm2', method_type: 'totp', label: 'Backup', verified_at: null, last_used_at: null, revoked_at: null },
  ],
};

describe('MfaChallengeDialog', () => {
  beforeEach(() => {
    completeMutation.mockReset();
  });

  it('submits code for selected method', async () => {
    const onSuccess = vi.fn();
    render(
      <MfaChallengeDialog open challenge={challenge as any} onClose={() => {}} onSuccess={onSuccess} />,
    );

    fireEvent.click(screen.getByText('Backup'));
    fireEvent.change(screen.getByPlaceholderText('123456'), { target: { value: '654321' } });
    fireEvent.click(screen.getByText('Verify'));

    await waitFor(() => expect(completeMutation).toHaveBeenCalled());
    expect(completeMutation).toHaveBeenCalledWith({
      challenge_token: 'token',
      method_id: 'm2',
      code: '654321',
    });
    expect(onSuccess).toHaveBeenCalled();
  });
});
