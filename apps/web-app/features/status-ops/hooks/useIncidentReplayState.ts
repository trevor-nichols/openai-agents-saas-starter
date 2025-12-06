import { useCallback, useMemo, useState } from 'react';

import type { IncidentRecord } from '@/types/status';

import type { DispatchSeverity } from '../constants';

export function getActiveIncidentId(selectedIncidentId: string | null, incidents: IncidentRecord[]): string {
  if (selectedIncidentId && incidents.some((incident) => incident.id === selectedIncidentId)) {
    return selectedIncidentId;
  }
  return incidents[0]?.id ?? '';
}

export interface IncidentReplayState {
  activeIncidentId: string;
  selectedIncidentId: string | null;
  severity: DispatchSeverity;
  tenantScope: string;
  setSelectedIncidentId: (incidentId: string | null) => void;
  setSeverity: (severity: DispatchSeverity) => void;
  setTenantScope: (tenantId: string) => void;
  clearTenantScope: () => void;
}

export function useIncidentReplayState(
  incidents: IncidentRecord[],
  initialTenantScope = '',
): IncidentReplayState {
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [severity, setSeverity] = useState<DispatchSeverity>('major');
  const [tenantScope, setTenantScope] = useState(initialTenantScope);

  const activeIncidentId = useMemo(
    () => getActiveIncidentId(selectedIncidentId, incidents),
    [incidents, selectedIncidentId],
  );

  const clearTenantScope = useCallback(() => setTenantScope(''), []);

  return {
    activeIncidentId,
    selectedIncidentId,
    severity,
    tenantScope,
    setSelectedIncidentId,
    setSeverity,
    setTenantScope,
    clearTenantScope,
  };
}
