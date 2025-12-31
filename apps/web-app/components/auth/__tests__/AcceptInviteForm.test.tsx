import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { AcceptInviteForm } from '../AcceptInviteForm';
import { TooltipProvider } from '@/components/ui/tooltip';

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    refresh: vi.fn(),
  }),
}));

const acceptTeamInviteAction = vi.fn();

vi.mock('@/app/actions/auth/team-invites', () => ({
  acceptTeamInviteAction: (...args: unknown[]) => acceptTeamInviteAction(...args),
}));

vi.mock('@/lib/queries/team', () => ({
  useAcceptTeamInviteExistingMutation: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
  }),
}));

const toast = vi.hoisted(() =>
  Object.assign(vi.fn(), {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    dismiss: vi.fn(),
  }),
);

vi.mock('sonner', () => ({
  toast,
}));

describe('AcceptInviteForm', () => {
  beforeEach(() => {
    acceptTeamInviteAction.mockReset();
  });

  it('requires an invite token', async () => {
    render(
      <TooltipProvider>
        <AcceptInviteForm />
      </TooltipProvider>,
    );

    fireEvent.input(screen.getByLabelText('Invite token'), { target: { value: '' } });
    fireEvent.input(screen.getByLabelText('Create password'), { target: { value: 'supersecurepassword' } });
    fireEvent.input(screen.getByLabelText('Confirm password'), { target: { value: 'supersecurepassword' } });

    fireEvent.click(screen.getByRole('button', { name: /accept invite/i }));

    expect(await screen.findByText('Invite token is required.')).toBeInTheDocument();
    expect(acceptTeamInviteAction).not.toHaveBeenCalled();
  });

  it('submits the invite acceptance payload', async () => {
    acceptTeamInviteAction.mockResolvedValueOnce(undefined);

    render(
      <TooltipProvider>
        <AcceptInviteForm initialToken="token-123" />
      </TooltipProvider>,
    );

    fireEvent.input(screen.getByLabelText('Create password'), { target: { value: 'supersecurepassword' } });
    fireEvent.input(screen.getByLabelText('Confirm password'), { target: { value: 'supersecurepassword' } });

    fireEvent.click(screen.getByRole('button', { name: /accept invite/i }));

    await waitFor(() => {
      expect(acceptTeamInviteAction).toHaveBeenCalledWith(
        expect.objectContaining({
          token: 'token-123',
          password: 'supersecurepassword',
          displayName: null,
        }),
        expect.any(Object),
      );
    });
  });

  it('surfaces server action errors', async () => {
    acceptTeamInviteAction.mockRejectedValueOnce(new Error('Invalid invite token'));

    render(
      <TooltipProvider>
        <AcceptInviteForm initialToken="token-123" />
      </TooltipProvider>,
    );

    fireEvent.input(screen.getByLabelText('Create password'), { target: { value: 'supersecurepassword' } });
    fireEvent.input(screen.getByLabelText('Confirm password'), { target: { value: 'supersecurepassword' } });

    fireEvent.click(screen.getByRole('button', { name: /accept invite/i }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalled();
    });
  });
});
