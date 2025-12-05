import { GlassPanel, InlineTag, SectionHeader } from '@/components/ui/foundation';
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import type { IncidentRecord } from '@/types/status';
import { formatDateOnly, incidentTone } from '../utils/statusFormatting';
import { IncidentSkeleton } from './skeletons';

interface IncidentTableProps {
  incidents: IncidentRecord[];
  showSkeletons: boolean;
}

export function IncidentTable({ incidents, showSkeletons }: IncidentTableProps) {
  return (
    <div className="space-y-4">
      <SectionHeader
        eyebrow="Incident log"
        title="Recent events"
        description="Full incident timelines live in Linear, but this snapshot keeps marketing visitors informed."
      />
      <GlassPanel>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Date</TableHead>
              <TableHead>Service</TableHead>
              <TableHead>Impact</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {showSkeletons
              ? [1, 2, 3].map((item) => <IncidentSkeleton key={`incident-skeleton-${item}`} />)
              : incidents.length > 0
                ? incidents.map((incident) => (
                    <TableRow key={incident.id}>
                      <TableCell className="font-medium">{formatDateOnly(incident.occurredAt)}</TableCell>
                      <TableCell>{incident.service}</TableCell>
                      <TableCell className="text-foreground/70">{incident.impact}</TableCell>
                      <TableCell>
                        <InlineTag tone={incidentTone(incident.state)}>{incident.state}</InlineTag>
                      </TableCell>
                    </TableRow>
                  ))
                : (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center text-sm text-foreground/60">
                        No incidents recorded in the current window.
                      </TableCell>
                    </TableRow>
                  )}
          </TableBody>
          <TableCaption>Incident metadata syncs nightly from the real status board.</TableCaption>
        </Table>
      </GlassPanel>
    </div>
  );
}
