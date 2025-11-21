'use client';

import { useMemo } from 'react';
import { AlertCircle, Send, ShieldCheck } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { GlassPanel, InlineTag } from '@/components/ui/foundation';
import { EmptyState } from '@/components/ui/states/EmptyState';
import { SkeletonPanel } from '@/components/ui/states/SkeletonPanel';
import type { IncidentRecord } from '@/types/status';

interface ResendIncidentPanelProps {
  incidents: IncidentRecord[];
  isLoadingIncidents: boolean;
  selectedIncidentId: string;
  severity: 'all' | 'major' | 'maintenance';
  tenantScope: string;
  onIncidentChange: (incidentId: string) => void;
  onSeverityChange: (severity: 'all' | 'major' | 'maintenance') => void;
  onTenantScopeChange: (tenantId: string) => void;
  onClearTenantScope: () => void;
  onSubmit: () => void;
  isSubmitting: boolean;
}

export function ResendIncidentPanel({
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
}: ResendIncidentPanelProps) {
  const incidentOptions = useMemo(() => {
    return incidents.map((incident) => ({
      id: incident.id,
      label: `${incident.service} • ${incident.impact}`,
      helper: incident.occurredAt,
      state: incident.state,
    }));
  }, [incidents]);

  if (isLoadingIncidents) {
    return <SkeletonPanel lines={8} />;
  }

  return (
    <GlassPanel className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-foreground/50">Delivery</p>
          <p className="text-base font-semibold text-foreground">Resend incident notifications</p>
          <p className="text-sm text-foreground/60">
            Replay the most recent incidents to subscribers that match your severity and tenant scope.
          </p>
        </div>
        <InlineTag tone={tenantScope ? 'positive' : 'default'}>
          {tenantScope ? 'Tenant scoped' : 'All tenants'}
        </InlineTag>
      </div>

      {incidentOptions.length === 0 ? (
        <EmptyState
          title="No incidents available"
          description="We haven't recorded any incidents in the current snapshot."
          icon={<AlertCircle className="h-5 w-5 text-foreground/50" />}
        />
      ) : (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Incident</Label>
            <Select value={selectedIncidentId} onValueChange={onIncidentChange}>
              <SelectTrigger>
                <SelectValue placeholder="Choose an incident" />
              </SelectTrigger>
              <SelectContent>
                {incidentOptions.map((option) => (
                  <SelectItem key={option.id} value={option.id}>
                    <div className="flex flex-col">
                      <span className="font-medium text-foreground">{option.label}</span>
                      <span className="text-xs text-foreground/60">
                        {new Date(option.helper).toLocaleString()}
                      </span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Severity filter</Label>
              <Select value={severity} onValueChange={(value) => onSeverityChange(value as 'all' | 'major' | 'maintenance')}>
                <SelectTrigger>
                  <SelectValue placeholder="Select severity" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="major">Major incidents</SelectItem>
                  <SelectItem value="all">All severities</SelectItem>
                  <SelectItem value="maintenance">Maintenance only</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="tenant-scope">Tenant scope (optional)</Label>
              <div className="flex items-center gap-2">
                <Input
                  id="tenant-scope"
                  placeholder="Tenant UUID"
                  value={tenantScope}
                  onChange={(event) => onTenantScopeChange(event.target.value)}
                />
                {tenantScope ? (
                  <Button type="button" variant="ghost" size="sm" onClick={onClearTenantScope}>
                    Clear
                  </Button>
                ) : null}
              </div>
              <p className="text-xs text-foreground/60">
                Leave blank to notify every subscriber; populate to target a single tenant.
              </p>
            </div>
          </div>

          <div className="flex items-center justify-between gap-3 rounded-xl border border-white/10 bg-white/5 px-3 py-2">
            <div className="flex items-center gap-2 text-sm text-foreground/70">
              <ShieldCheck className="h-4 w-4" aria-hidden />
              <span>
                Requires <span className="font-semibold">status:manage</span> scope
              </span>
            </div>
            <Button
              onClick={onSubmit}
              disabled={isSubmitting || incidentOptions.length === 0}
            >
              <Send className="h-4 w-4" aria-hidden />
              {isSubmitting ? 'Dispatching…' : 'Resend incident'}
            </Button>
          </div>
        </div>
      )}
    </GlassPanel>
  );
}
