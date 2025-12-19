'use client';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

import type { AssetFilterDraft } from '../hooks/useAssetLibrary';

interface AssetFiltersProps {
  draft: AssetFilterDraft;
  onChange: (next: AssetFilterDraft) => void;
  onApply: () => void;
  onClear: () => void;
  disabled?: boolean;
}

export function AssetFilters({ draft, onChange, onApply, onClear, disabled }: AssetFiltersProps) {
  const hasFilters =
    Boolean(draft.conversationId) ||
    Boolean(draft.agentKey) ||
    Boolean(draft.sourceTool) ||
    Boolean(draft.mimeTypePrefix) ||
    Boolean(draft.createdAfter) ||
    Boolean(draft.createdBefore);

  return (
    <div className="grid gap-4 lg:grid-cols-[1.5fr_1fr_1fr_1fr]">
      <div className="space-y-1">
        <Label className="text-xs text-foreground/70">Conversation</Label>
        <Input
          value={draft.conversationId}
          onChange={(event) => onChange({ ...draft, conversationId: event.target.value })}
          placeholder="conversation-id"
          disabled={disabled}
        />
      </div>

      <div className="space-y-1">
        <Label className="text-xs text-foreground/70">Source tool</Label>
        <Select
          value={draft.sourceTool || 'all'}
          onValueChange={(value) =>
            onChange({
              ...draft,
              sourceTool: value === 'all' ? '' : (value as AssetFilterDraft['sourceTool']),
            })
          }
          disabled={disabled}
        >
          <SelectTrigger>
            <SelectValue placeholder="All sources" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All sources</SelectItem>
            <SelectItem value="image_generation">Image generation</SelectItem>
            <SelectItem value="code_interpreter">Code interpreter</SelectItem>
            <SelectItem value="user_upload">User upload</SelectItem>
            <SelectItem value="unknown">Unknown</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-1">
        <Label className="text-xs text-foreground/70">Agent key</Label>
        <Input
          value={draft.agentKey}
          onChange={(event) => onChange({ ...draft, agentKey: event.target.value })}
          placeholder="agent key"
          disabled={disabled}
        />
      </div>

      <div className="space-y-1">
        <Label className="text-xs text-foreground/70">MIME prefix</Label>
        <Input
          value={draft.mimeTypePrefix}
          onChange={(event) => onChange({ ...draft, mimeTypePrefix: event.target.value })}
          placeholder="image/ or application/pdf"
          disabled={disabled}
        />
      </div>

      <div className="space-y-1">
        <Label className="text-xs text-foreground/70">Created after</Label>
        <Input
          type="date"
          value={draft.createdAfter}
          onChange={(event) => onChange({ ...draft, createdAfter: event.target.value })}
          disabled={disabled}
        />
      </div>

      <div className="space-y-1">
        <Label className="text-xs text-foreground/70">Created before</Label>
        <Input
          type="date"
          value={draft.createdBefore}
          onChange={(event) => onChange({ ...draft, createdBefore: event.target.value })}
          disabled={disabled}
        />
      </div>

      <div className="flex items-end gap-2">
        <Button size="sm" variant="secondary" onClick={onApply} disabled={disabled}>
          Apply
        </Button>
        <Button
          size="sm"
          variant="ghost"
          onClick={onClear}
          disabled={disabled || !hasFilters}
        >
          Clear
        </Button>
      </div>
    </div>
  );
}
