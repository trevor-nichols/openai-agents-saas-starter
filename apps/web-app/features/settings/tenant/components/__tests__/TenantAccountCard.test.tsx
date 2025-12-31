import type { ComponentProps } from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { TenantAccount } from '@/types/tenantAccount';
import { TenantAccountCard } from '../TenantAccountCard';

const toastMocks = {
  success: vi.fn(),
  error: vi.fn(),
  info: vi.fn(),
  message: vi.fn(),
  dismiss: vi.fn(),
};

vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => toastMocks,
}));

const SAMPLE_ACCOUNT: TenantAccount = {
  id: 'tenant-1',
  slug: 'acme',
  name: 'Acme',
  status: 'active',
  createdAt: '2025-12-01T00:00:00Z',
  updatedAt: '2025-12-02T00:00:00Z',
  statusUpdatedAt: null,
  suspendedAt: null,
  deprovisionedAt: null,
};

function renderTenantAccountCard(overrides?: Partial<ComponentProps<typeof TenantAccountCard>>) {
  const props = {
    account: SAMPLE_ACCOUNT,
    isLoading: false,
    error: null,
    isSaving: false,
    onRetry: vi.fn(),
    onSubmit: vi.fn().mockResolvedValue(undefined),
    ...overrides,
  };

  render(<TenantAccountCard {...props} />);
  return props;
}

describe('TenantAccountCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('enables save once the tenant name changes', async () => {
    const user = userEvent.setup();
    const { onSubmit } = renderTenantAccountCard();

    const saveButton = screen.getByRole('button', { name: 'Save changes' });
    expect(saveButton).toBeDisabled();

    const input = screen.getByPlaceholderText('Tenant name');
    await user.clear(input);
    await user.type(input, 'Acme Labs');

    expect(saveButton).toBeEnabled();
    await user.click(saveButton);

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({ name: 'Acme Labs' });
    });
  });

  it('requires a tenant name before saving', async () => {
    const user = userEvent.setup();
    const { onSubmit } = renderTenantAccountCard();

    const saveButton = screen.getByRole('button', { name: 'Save changes' });
    const input = screen.getByPlaceholderText('Tenant name');

    await user.clear(input);
    expect(saveButton).toBeEnabled();

    await user.click(saveButton);

    expect(onSubmit).not.toHaveBeenCalled();
    expect(toastMocks.error).toHaveBeenCalledWith(
      expect.objectContaining({ title: 'Name is required' }),
    );
  });

  it('renders the error state and retries when requested', async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();

    renderTenantAccountCard({
      account: null,
      error: new Error('Unable to load tenant account'),
      onRetry,
    });

    expect(screen.getByText('Tenant account unavailable')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Retry' }));

    expect(onRetry).toHaveBeenCalled();
  });
});
