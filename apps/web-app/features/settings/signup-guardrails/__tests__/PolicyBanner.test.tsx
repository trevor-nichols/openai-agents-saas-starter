import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { PolicyBanner } from '../components/PolicyBanner';
import type { SignupAccessPolicy } from '@/types/signup';

vi.mock('sonner', () => ({
  toast: vi.fn(),
  success: vi.fn(),
  error: vi.fn(),
  info: vi.fn(),
  dismiss: vi.fn(),
}));

const policyFixture = (mode: 'public' | 'invite_only' | 'approval'): SignupAccessPolicy => ({
  policy: mode,
  invite_required: mode !== 'public',
  request_access_enabled: mode !== 'public',
});

describe('PolicyBanner', () => {
  it('renders invite-only status copy', () => {
    render(<PolicyBanner policy={policyFixture('invite_only')} />);

    expect(screen.getByText('Invite only')).toBeInTheDocument();
    expect(screen.getByText(/Registration requires an invite token/i)).toBeInTheDocument();
  });

  it('renders error state', () => {
    render(<PolicyBanner error="boom" />);

    expect(screen.getByText('Unable to load policy')).toBeInTheDocument();
    expect(screen.getByText('boom')).toBeInTheDocument();
  });
});
