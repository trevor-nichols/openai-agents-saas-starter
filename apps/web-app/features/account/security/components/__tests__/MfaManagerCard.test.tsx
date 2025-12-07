import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';

import { MfaManagerCard } from '../MfaManagerCard';

const methodsQuery = vi.hoisted(() => vi.fn());
const revokeMutation = vi.hoisted(() => vi.fn());
const regenMutation = vi.hoisted(() => vi.fn());
const startMutation = vi.hoisted(() => vi.fn());
const verifyMutation = vi.hoisted(() => vi.fn());

vi.mock('@/lib/queries/mfa', () => ({
  useMfaMethodsQuery: () => ({ data: [{ id: 'm1', method_type: 'totp', label: 'Primary', verified_at: 'now', last_used_at: null, revoked_at: null }], isLoading: false, refetch: methodsQuery }),
  useRevokeMfaMethodMutation: () => ({ mutateAsync: revokeMutation, isPending: false }),
  useRegenerateRecoveryCodesMutation: () => ({ mutateAsync: regenMutation, isPending: false }),
  useStartTotpEnrollmentMutation: () => ({ mutateAsync: startMutation, isPending: false }),
  useVerifyTotpMutation: () => ({ mutateAsync: verifyMutation, isPending: false }),
}));

describe('MfaManagerCard', () => {
  beforeEach(() => {
    revokeMutation.mockReset();
    regenMutation.mockReset();
    startMutation.mockReset();
    verifyMutation.mockReset();
    methodsQuery.mockReset();
  });

  it('revokes a method', async () => {
    render(<MfaManagerCard />);
    fireEvent.click(screen.getByText('Revoke'));
    await waitFor(() => expect(revokeMutation).toHaveBeenCalledWith('m1'));
  });

  it('starts enrollment when Add TOTP clicked', async () => {
    startMutation.mockResolvedValue({ secret: 'abc', method_id: 'mid', otpauth_url: null });
    render(<MfaManagerCard />);
    fireEvent.click(screen.getByText('Add TOTP'));
    await waitFor(() => expect(startMutation).toHaveBeenCalled());
  });

  it('regenerates recovery codes', async () => {
    regenMutation.mockResolvedValue({ codes: ['a', 'b', 'c'] });
    render(<MfaManagerCard />);
    fireEvent.click(screen.getByText('Regenerate recovery codes'));
    await waitFor(() => expect(regenMutation).toHaveBeenCalled());
  });
});
