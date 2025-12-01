import { Info } from 'lucide-react';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { InlineTag } from '@/components/ui/foundation';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import type { LocationHint } from '@/lib/api/client/types.gen';

type LocationOptInProps = {
  id?: string;
  shareLocation: boolean;
  onShareLocationChange: (value: boolean) => void;
  location: LocationHint;
  onLocationChange: (field: keyof LocationHint, value: string) => void;
  disabled?: boolean;
  label?: string;
  showOptionalBadge?: boolean;
  tooltipText?: string;
};

/**
 * Reusable location opt-in control for hosted web search biasing.
 * Keeps UX consistent across chat, workflows, and future surfaces.
 */
export function LocationOptIn({
  id = 'share-location',
  shareLocation,
  onShareLocationChange,
  location,
  onLocationChange,
  disabled = false,
  label = 'Bias web search with approximate location',
  showOptionalBadge = true,
  tooltipText = 'City/region/country/timezone are trimmed, optional, and only sent when toggled on to bias web search.',
}: LocationOptInProps) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <Switch
          id={id}
          checked={shareLocation}
          onCheckedChange={onShareLocationChange}
          disabled={disabled}
        />
        <Label htmlFor={id} className="text-xs font-medium text-foreground/80">
          {label}
        </Label>
        {showOptionalBadge ? <InlineTag tone="default">Optional</InlineTag> : null}
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                type="button"
                className="text-foreground/60 transition hover:text-foreground"
                aria-label="How location is used"
                disabled={disabled}
              >
                <Info size={14} strokeWidth={1.75} />
              </button>
            </TooltipTrigger>
            <TooltipContent side="top">{tooltipText}</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      {shareLocation ? (
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          <Input
            placeholder="City"
            value={location.city ?? ''}
            onChange={(event) => onLocationChange('city', event.target.value)}
            disabled={disabled}
          />
          <Input
            placeholder="Region/State"
            value={location.region ?? ''}
            onChange={(event) => onLocationChange('region', event.target.value)}
            disabled={disabled}
          />
          <Input
            placeholder="Country"
            value={location.country ?? ''}
            onChange={(event) => onLocationChange('country', event.target.value)}
            disabled={disabled}
          />
          <Input
            placeholder="Timezone (e.g., America/Chicago)"
            value={location.timezone ?? ''}
            onChange={(event) => onLocationChange('timezone', event.target.value)}
            disabled={disabled}
            title="IANA timezone, e.g., America/Chicago"
          />
        </div>
      ) : null}
    </div>
  );
}

export default LocationOptIn;

export type { LocationHint };
