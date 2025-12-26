'use client';

import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

import { UNASSIGNED_OPTION } from '../../constants';
import type { SelectOption } from '../../types';

interface AgentSelectorProps {
  value: string | null;
  options: SelectOption[];
  isLoading: boolean;
  error: Error | null;
  onChange: (value: string | null) => void;
}

export function AgentSelector({ value, options, isLoading, error, onChange }: AgentSelectorProps) {
  const placeholder = isLoading
    ? 'Loading agents…'
    : options.length
      ? 'Select an agent'
      : 'No file_search agents';

  return (
    <div className="space-y-1">
      <Label className="text-[11px] uppercase tracking-wide text-foreground/60">
        Agent (file_search)
      </Label>
      <Select
        value={value ?? UNASSIGNED_OPTION}
        onValueChange={(nextValue) => {
          const next = nextValue === UNASSIGNED_OPTION ? null : nextValue;
          onChange(next);
        }}
        disabled={isLoading || Boolean(error)}
      >
        <SelectTrigger>
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={UNASSIGNED_OPTION}>No agent gating</SelectItem>
          {options.map((agent) => (
            <SelectItem key={agent.value} value={agent.value}>
              <div className="space-y-1">
                <div className="font-medium">{agent.label}</div>
                {agent.description ? (
                  <div className="text-xs text-muted-foreground">{agent.description}</div>
                ) : null}
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {error ? <p className="text-xs text-destructive">Unable to load agents.</p> : null}
    </div>
  );
}
