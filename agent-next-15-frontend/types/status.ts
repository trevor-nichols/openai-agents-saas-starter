import type {
  IncidentSchema,
  PlatformStatusResponse,
  ServiceStatusSchema,
  StatusOverviewSchema,
  UptimeMetricSchema,
} from '@/lib/api/client/types.gen';

export type RawStatusOverview = StatusOverviewSchema;
export type RawServiceStatus = ServiceStatusSchema;
export type RawIncidentRecord = IncidentSchema;
export type RawUptimeMetric = UptimeMetricSchema;
export type RawPlatformStatusResponse = PlatformStatusResponse;

export interface StatusOverview {
  state: string;
  description: string;
  updatedAt: string;
}

export interface ServiceStatus {
  name: string;
  status: string;
  description: string;
  owner: string;
  lastIncidentAt: string | null;
}

export interface IncidentRecord {
  id: string;
  service: string;
  occurredAt: string;
  impact: string;
  state: string;
}

export interface UptimeMetric {
  label: string;
  value: string;
  helperText: string;
  trendValue: string;
  trendTone: string;
}

export interface PlatformStatusSnapshot {
  generatedAt: string;
  overview: StatusOverview;
  services: ServiceStatus[];
  incidents: IncidentRecord[];
  uptimeMetrics: UptimeMetric[];
}

export function mapPlatformStatusResponse(raw: RawPlatformStatusResponse): PlatformStatusSnapshot {
  return {
    generatedAt: raw.generated_at,
    overview: {
      state: raw.overview.state,
      description: raw.overview.description,
      updatedAt: raw.overview.updated_at,
    },
    services: raw.services.map((service) => ({
      name: service.name,
      status: service.status,
      description: service.description,
      owner: service.owner,
      lastIncidentAt: service.last_incident_at ?? null,
    })),
    incidents: raw.incidents.map((incident) => ({
      id: incident.incident_id,
      service: incident.service,
      occurredAt: incident.occurred_at,
      impact: incident.impact,
      state: incident.state,
    })),
    uptimeMetrics: raw.uptime_metrics.map((metric) => ({
      label: metric.label,
      value: metric.value,
      helperText: metric.helper_text,
      trendValue: metric.trend_value,
      trendTone: metric.trend_tone,
    })),
  };
}
