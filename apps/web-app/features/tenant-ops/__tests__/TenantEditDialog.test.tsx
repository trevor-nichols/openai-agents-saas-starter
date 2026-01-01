import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import type { TenantAccountOperatorSummary } from '@/types/tenantAccount';
import { TenantEditDialog } from '../components/TenantEditDialog';

const SAMPLE_TENANT: TenantAccountOperatorSummary = {
  id: 'tenant-1',
  slug: 'acme',
  name: 'Acme',
  status: 'active',
  createdAt: '2025-12-01T00:00:00Z',
  updatedAt: '2025-12-02T00:00:00Z',
  statusUpdatedAt: null,
  suspendedAt: null,
  deprovisionedAt: null,
  statusReason: null,
  statusUpdatedBy: null,
};

describe('TenantEditDialog', () => {
  it('blocks clearing a slug once set', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue(undefined);

    render(
      <TenantEditDialog
        open={true}
        onOpenChange={() => {}}
        tenant={SAMPLE_TENANT}
        onSubmit={onSubmit}
        isSubmitting={false}
      />,
    );

    const slugInput = screen.getByLabelText('Slug');
    await waitFor(() => expect(slugInput).toHaveValue('acme'));

    await user.clear(slugInput);
    await user.click(screen.getByRole('button', { name: 'Save changes' }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(await screen.findByText('Slug cannot be cleared once set.')).toBeInTheDocument();
  });
});
