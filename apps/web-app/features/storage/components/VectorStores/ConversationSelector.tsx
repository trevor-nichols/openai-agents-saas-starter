'use client';

import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

import { UNASSIGNED_OPTION } from '../../constants';
import type { SelectOption } from '../../types';

interface ConversationSelectorProps {
  value: string | null;
  options: SelectOption[];
  isLoading: boolean;
  error: Error | null;
  hasAgent: boolean;
  onChange: (value: string | null) => void;
}

export function ConversationSelector({
  value,
  options,
  isLoading,
  error,
  hasAgent,
  onChange,
}: ConversationSelectorProps) {
  const placeholder = !hasAgent
    ? 'Select an agent first'
    : isLoading
      ? 'Loading conversations…'
      : options.length
        ? 'Select a conversation'
        : 'No conversations found';

  return (
    <div className="space-y-1">
      <Label className="text-[11px] uppercase tracking-wide text-foreground/60">Conversation</Label>
      <Select
        value={value ?? UNASSIGNED_OPTION}
        onValueChange={(nextValue) =>
          onChange(nextValue === UNASSIGNED_OPTION ? null : nextValue)
        }
        disabled={!hasAgent || isLoading || Boolean(error)}
      >
        <SelectTrigger>
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={UNASSIGNED_OPTION}>No conversation</SelectItem>
          {options.map((conversation) => (
            <SelectItem key={conversation.value} value={conversation.value}>
              <div className="space-y-1">
                <div className="font-medium">{conversation.label}</div>
                {conversation.description ? (
                  <div className="text-xs text-muted-foreground">{conversation.description}</div>
                ) : null}
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {error ? <p className="text-xs text-destructive">Unable to load conversations.</p> : null}
    </div>
  );
}
