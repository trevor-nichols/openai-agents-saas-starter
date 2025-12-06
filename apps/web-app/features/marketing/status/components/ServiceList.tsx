import { GlassPanel, InlineTag } from '@/components/ui/foundation';
import type { ServiceStatus } from '@/types/status';
import { resolveTone, statusLabel, formatTimestamp } from '../utils/statusFormatting';
import { ServiceSkeleton } from './skeletons';

interface ServiceListProps {
  services: ServiceStatus[];
  showSkeletons: boolean;
}

export function ServiceList({ services, showSkeletons }: ServiceListProps) {
  if (showSkeletons) {
    return (
      <div className="space-y-6">
        {[1, 2, 3].map((item) => (
          <ServiceSkeleton key={`service-skeleton-${item}`} />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {services.map((service) => (
        <GlassPanel key={service.name} className="space-y-4">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h3 className="text-lg font-semibold text-foreground">{service.name}</h3>
              <p className="text-sm text-foreground/60">{service.description}</p>
            </div>
            <InlineTag tone={resolveTone(service.status)}>{statusLabel(service.status)}</InlineTag>
          </div>
          <div className="flex flex-wrap items-center justify-between text-xs text-foreground/60">
            <span>Owner · {service.owner}</span>
            <span>Last incident · {formatTimestamp(service.lastIncidentAt)}</span>
          </div>
        </GlassPanel>
      ))}
    </div>
  );
}
