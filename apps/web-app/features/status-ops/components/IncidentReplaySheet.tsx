'use client';

import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import type { IncidentRecord } from '@/types/status';

import type { DispatchSeverity } from '../constants';
import { ResendIncidentPanel } from './ResendIncidentPanel';

interface IncidentReplaySheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  incidents: IncidentRecord[];
  isLoadingIncidents: boolean;
  selectedIncidentId: string;
  severity: DispatchSeverity;
  tenantScope: string;
  onIncidentChange: (incidentId: string) => void;
  onSeverityChange: (severity: DispatchSeverity) => void;
  onTenantScopeChange: (tenantId: string) => void;
  onClearTenantScope: () => void;
  onSubmit: () => void;
  isSubmitting: boolean;
}

export function IncidentReplaySheet({
  open,
  onOpenChange,
  incidents,
  isLoadingIncidents,
  selectedIncidentId,
  severity,
  tenantScope,
  onIncidentChange,
  onSeverityChange,
  onTenantScopeChange,
  onClearTenantScope,
  onSubmit,
  isSubmitting,
}: IncidentReplaySheetProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetTrigger asChild>
        <Button>Replay incident</Button>
      </SheetTrigger>
      <SheetContent side="right" className="w-full sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>Replay incident</SheetTitle>
        </SheetHeader>
        <div className="mt-4">
          <ResendIncidentPanel
            incidents={incidents}
            isLoadingIncidents={isLoadingIncidents}
            selectedIncidentId={selectedIncidentId}
            severity={severity}
            tenantScope={tenantScope}
            onIncidentChange={onIncidentChange}
            onSeverityChange={onSeverityChange}
            onTenantScopeChange={onTenantScopeChange}
            onClearTenantScope={onClearTenantScope}
            onSubmit={onSubmit}
            isSubmitting={isSubmitting}
          />
        </div>
      </SheetContent>
    </Sheet>
  );
}
