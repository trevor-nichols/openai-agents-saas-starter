import { CreditCard, MoreHorizontal } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import type { BillingPaymentMethod } from '@/lib/types/billing';

import { formatCardBrand, formatCardExpiry } from '../../shared/utils/formatters';

interface PaymentMethodRowProps {
  method: BillingPaymentMethod;
  isSettingDefault: boolean;
  isDetaching: boolean;
  canRemove: boolean;
  onSetDefault: (paymentMethodId: string) => void;
  onRequestDetach: (method: BillingPaymentMethod) => void;
}

export function PaymentMethodRow({
  method,
  isSettingDefault,
  isDetaching,
  canRemove,
  onSetDefault,
  onRequestDetach,
}: PaymentMethodRowProps) {
  const isDefault = Boolean(method.is_default);

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/5 bg-white/5 p-4">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/10">
          <CreditCard className="h-5 w-5 text-foreground/70" />
        </div>
        <div>
          <p className="text-sm font-semibold text-foreground">
            {formatCardBrand(method.brand)} ·••• {method.last4 ?? '—'}
          </p>
          <p className="text-xs text-foreground/60">
            Expires {formatCardExpiry(method.exp_month, method.exp_year)}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {isDefault ? <Badge variant="secondary">Default</Badge> : null}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" aria-label="Payment method actions">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem
              disabled={isDefault || isSettingDefault}
              onClick={() => onSetDefault(method.id)}
            >
              {isSettingDefault ? 'Updating…' : 'Make default'}
            </DropdownMenuItem>
            <DropdownMenuItem
              disabled={!canRemove || isDetaching}
              onClick={() => onRequestDetach(method)}
            >
              {isDetaching ? 'Removing…' : 'Remove'}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}
