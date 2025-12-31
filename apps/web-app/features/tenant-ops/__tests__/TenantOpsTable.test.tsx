import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';

import { TenantOpsTable } from '../components/TenantOpsTable';
import type { TenantAccountOperatorSummary } from '@/types/tenantAccount';

const SAMPLE_TENANTS: TenantAccountOperatorSummary[] = [
  {
    id: 'tenant-active',
    slug: 'active',
    name: 'Active Tenant',
    status: 'active',
    createdAt: '2025-12-01T00:00:00Z',
    updatedAt: '2025-12-02T00:00:00Z',
    statusUpdatedAt: null,
    suspendedAt: null,
    deprovisionedAt: null,
    statusReason: null,
    statusUpdatedBy: null,
  },
  {
    id: 'tenant-suspended',
    slug: 'suspended',
    name: 'Suspended Tenant',
    status: 'suspended',
    createdAt: '2025-12-01T00:00:00Z',
    updatedAt: '2025-12-02T00:00:00Z',
    statusUpdatedAt: null,
    suspendedAt: '2025-12-03T00:00:00Z',
    deprovisionedAt: null,
    statusReason: 'policy',
    statusUpdatedBy: 'operator',
  },
  {
    id: 'tenant-deprovisioned',
    slug: 'deprovisioned',
    name: 'Deprovisioned Tenant',
    status: 'deprovisioned',
    createdAt: '2025-12-01T00:00:00Z',
    updatedAt: '2025-12-02T00:00:00Z',
    statusUpdatedAt: null,
    suspendedAt: null,
    deprovisionedAt: '2025-12-04T00:00:00Z',
    statusReason: 'ended',
    statusUpdatedBy: 'operator',
  },
];

describe('TenantOpsTable', () => {
  it('renders lifecycle actions based on tenant status', () => {
    const onAction = vi.fn();
    const onSelect = vi.fn();
    render(
      <TenantOpsTable
        tenants={SAMPLE_TENANTS}
        selectedTenantId="tenant-suspended"
        onSelect={onSelect}
        onAction={onAction}
      />,
    );

    expect(screen.getByRole('button', { name: 'Suspend' })).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Deprovision' })).toHaveLength(2);
    expect(screen.getByRole('button', { name: 'Reactivate' })).toBeInTheDocument();
    expect(screen.getByText('No actions')).toBeInTheDocument();

    const selectedRow = screen.getByText('Suspended Tenant').closest('tr');
    expect(selectedRow).toHaveAttribute('data-state', 'selected');
  });

  it('disables lifecycle actions when busy', () => {
    render(
      <TenantOpsTable
        tenants={SAMPLE_TENANTS}
        selectedTenantId="tenant-active"
        onSelect={() => {}}
        onAction={() => {}}
        isBusy={true}
      />,
    );

    expect(screen.getByRole('button', { name: 'Suspend' })).toBeDisabled();
    expect(screen.getAllByRole('button', { name: 'Deprovision' })[0]).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Reactivate' })).toBeDisabled();
  });
});
