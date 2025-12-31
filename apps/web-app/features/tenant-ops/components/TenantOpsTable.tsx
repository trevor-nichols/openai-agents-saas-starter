'use client';

import { Button } from '@/components/ui/button';
import { InlineTag } from '@/components/ui/foundation';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { formatDateTime } from '@/lib/utils/time';
import type { TenantAccountOperatorSummary } from '@/types/tenantAccount';

import { TENANT_STATUS_LABELS, TENANT_STATUS_TONES } from '../constants';
import type { TenantLifecycleAction } from '../types';
import { resolveLifecycleActions } from '../utils';

interface TenantOpsTableProps {
  tenants: TenantAccountOperatorSummary[];
  selectedTenantId?: string | null;
  onSelect: (tenantId: string) => void;
  onViewDetails?: (tenantId: string) => void;
  onAction: (action: TenantLifecycleAction, tenant: TenantAccountOperatorSummary) => void;
  isBusy?: boolean;
}

export function TenantOpsTable({
  tenants,
  selectedTenantId,
  onSelect,
  onViewDetails,
  onAction,
  isBusy = false,
}: TenantOpsTableProps) {
  return (
    <div className="overflow-hidden rounded-2xl border border-white/10">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Tenant</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Updated</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {tenants.map((tenant) => {
            const actions = resolveLifecycleActions(tenant.status);
            const isSelected = tenant.id === selectedTenantId;
            return (
              <TableRow
                key={tenant.id}
                data-state={isSelected ? 'selected' : undefined}
                className="cursor-pointer"
                onClick={() => onSelect(tenant.id)}
              >
                <TableCell>
                  <div className="space-y-1">
                    <p className="font-medium text-foreground">{tenant.name}</p>
                    <p className="text-xs text-foreground/60">Slug · {tenant.slug}</p>
                  </div>
                </TableCell>
                <TableCell>
                  <InlineTag tone={TENANT_STATUS_TONES[tenant.status] ?? 'default'}>
                    {TENANT_STATUS_LABELS[tenant.status] ?? tenant.status}
                  </InlineTag>
                </TableCell>
                <TableCell className="text-foreground/70">{formatDateTime(tenant.updatedAt)}</TableCell>
                <TableCell>
                  <div className="flex flex-wrap justify-end gap-2">
                    {onViewDetails ? (
                      <Button
                        size="sm"
                        variant="ghost"
                        className="md:hidden"
                        onClick={(event) => {
                          event.stopPropagation();
                          onViewDetails(tenant.id);
                        }}
                      >
                        Details
                      </Button>
                    ) : null}
                    {actions.length === 0 ? (
                      <span className="text-xs text-foreground/50">No actions</span>
                    ) : (
                      actions.map((action) => (
                        <Button
                          key={action}
                          size="sm"
                          variant={action === 'deprovision' ? 'destructive' : 'outline'}
                          disabled={isBusy}
                          onClick={(event) => {
                            event.stopPropagation();
                            onAction(action, tenant);
                          }}
                        >
                          {action === 'suspend' && 'Suspend'}
                          {action === 'reactivate' && 'Reactivate'}
                          {action === 'deprovision' && 'Deprovision'}
                        </Button>
                      ))
                    )}
                  </div>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
