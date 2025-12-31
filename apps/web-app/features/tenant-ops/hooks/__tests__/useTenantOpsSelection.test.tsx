import { act, renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import type { TenantAccountOperatorSummary } from '@/types/tenantAccount';

import { useTenantOpsSelection } from '../useTenantOpsSelection';

const baseTenant: TenantAccountOperatorSummary = {
  id: 'tenant-1',
  name: 'Acme',
  slug: 'acme',
  status: 'active',
  createdAt: '2025-01-01T00:00:00Z',
  updatedAt: '2025-01-02T00:00:00Z',
  statusUpdatedAt: null,
  suspendedAt: null,
  deprovisionedAt: null,
  statusReason: null,
  statusUpdatedBy: null,
};

describe('useTenantOpsSelection', () => {
  it('prefers the selected tenant and falls back when removed', () => {
    const tenants = [baseTenant, { ...baseTenant, id: 'tenant-2', slug: 'beta', name: 'Beta' }];
    const { result, rerender } = renderHook(
      ({ tenantList, mobile }) => useTenantOpsSelection({ tenants: tenantList, isMobile: mobile }),
      {
        initialProps: {
          tenantList: tenants,
          mobile: true,
        },
      },
    );

    expect(result.current.resolvedTenantId).toBe('tenant-1');

    act(() => {
      result.current.selectTenant('tenant-2');
    });

    expect(result.current.selectedTenantId).toBe('tenant-2');
    expect(result.current.resolvedTenantId).toBe('tenant-2');

    rerender({ tenantList: [baseTenant], mobile: true });

    expect(result.current.selectedTenantId).toBeNull();
    expect(result.current.resolvedTenantId).toBe('tenant-1');
  });

  it('opens details only on mobile', () => {
    const tenants = [baseTenant];

    const { result: mobileResult } = renderHook(() =>
      useTenantOpsSelection({ tenants, isMobile: true }),
    );

    act(() => {
      mobileResult.current.openDetails('tenant-1');
    });

    expect(mobileResult.current.detailOpen).toBe(true);

    const { result: desktopResult } = renderHook(() =>
      useTenantOpsSelection({ tenants, isMobile: false }),
    );

    act(() => {
      desktopResult.current.openDetails('tenant-1');
    });

    expect(desktopResult.current.detailOpen).toBe(false);
  });
});
