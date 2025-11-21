import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { RegisterForm } from '../RegisterForm';
import type { SignupAccessPolicy } from '@/types/signup';

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    refresh: vi.fn(),
  }),
}));

const registerTenantAction = vi.fn();

vi.mock('@/app/actions/auth/signup', () => ({
  registerTenantAction: (...args: unknown[]) => registerTenantAction(...args),
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

const buildPolicy = (mode: 'public' | 'invite_only' | 'approval'): SignupAccessPolicy => ({
  policy: mode,
  invite_required: mode !== 'public',
  request_access_enabled: mode !== 'public',
});

describe('RegisterForm', () => {
  beforeEach(() => {
    registerTenantAction.mockReset();
  });

  it('requires invite token when policy is not public', async () => {
    render(<RegisterForm policy={buildPolicy('invite_only')} requestAccessHref="/request-access" />);

    fireEvent.input(screen.getByLabelText('Full name'), { target: { value: 'Ada Lovelace' } });
    fireEvent.input(screen.getByLabelText('Organization'), { target: { value: 'Ada Labs' } });
    fireEvent.input(screen.getByLabelText('Email'), { target: { value: 'ada@example.com' } });
    fireEvent.input(screen.getByLabelText('Password'), { target: { value: 'supersecurepassword' } });
    fireEvent.click(screen.getByRole('checkbox', { name: /i agree/i }));

    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    expect(await screen.findByText('Invite token is required.')).toBeInTheDocument();
    expect(registerTenantAction).not.toHaveBeenCalled();
  });

  it('submits invite token when provided', async () => {
    registerTenantAction.mockResolvedValueOnce(undefined);
    render(<RegisterForm policy={buildPolicy('invite_only')} requestAccessHref="/request-access" />);

    fireEvent.input(screen.getByLabelText('Full name'), { target: { value: 'Grace Hopper' } });
    fireEvent.input(screen.getByLabelText('Organization'), { target: { value: 'Fleet Ops' } });
    fireEvent.input(screen.getByLabelText('Email'), { target: { value: 'grace@example.com' } });
    fireEvent.input(screen.getByLabelText('Password'), { target: { value: 'anothersecurepassword' } });
    fireEvent.input(screen.getByLabelText(/Invite token/i), { target: { value: 'token-123' } });
    fireEvent.click(screen.getByRole('checkbox', { name: /i agree/i }));

    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(registerTenantAction).toHaveBeenCalledWith(
        expect.objectContaining({ invite_token: 'token-123' }),
        expect.any(Object),
      );
    });
  });
});
