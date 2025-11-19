'use client';

import { useEffect, useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { GlassPanel, SectionHeader } from '@/components/ui/foundation';
import { Input } from '@/components/ui/input';
import { useToast } from '@/components/ui/use-toast';

import { recordToEntries, entriesToRecord } from '../utils';
import type { PlanMetadataEntry } from '../types';

interface PlanMetadataCardProps {
  planMetadata: Record<string, string>;
  isSaving: boolean;
  onSubmit: (metadata: Record<string, string>) => Promise<void>;
}

export function PlanMetadataCard({ planMetadata, isSaving, onSubmit }: PlanMetadataCardProps) {
  const toast = useToast();
  const [entries, setEntries] = useState<PlanMetadataEntry[]>(() => recordToEntries(planMetadata));

  useEffect(() => {
    setEntries(recordToEntries(planMetadata));
  }, [planMetadata]);

  const serializedOriginal = useMemo(() => JSON.stringify(planMetadata), [planMetadata]);
  const serializedCurrent = useMemo(() => JSON.stringify(entriesToRecord(entries)), [entries]);
  const isDirty = serializedCurrent !== serializedOriginal;

  const updateEntry = (id: string, field: 'key' | 'value', value: string) => {
    setEntries((prev) => prev.map((entry) => (entry.id === id ? { ...entry, [field]: value } : entry)));
  };

  const addEntry = () => {
    setEntries((prev) => [
      ...prev,
      {
        id: crypto.randomUUID?.() ?? Math.random().toString(36).slice(2, 10),
        key: '',
        value: '',
      },
    ]);
  };

  const removeEntry = (id: string) => {
    setEntries((prev) => prev.filter((entry) => entry.id !== id));
  };

  const handleSave = async () => {
    try {
      await onSubmit(entriesToRecord(entries));
      toast.success({
        title: 'Plan metadata updated',
        description: 'Overrides synced successfully.',
      });
    } catch (error) {
      toast.error({
        title: 'Unable to update plan metadata',
        description: error instanceof Error ? error.message : 'Try again shortly.',
      });
    }
  };

  const handleReset = () => {
    setEntries(recordToEntries(planMetadata));
  };

  return (
    <GlassPanel className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <SectionHeader
          eyebrow="Plans"
          title="Plan metadata"
          description="Override plan code, seat limits, or attach notes used by automation."
        />
        <div className="flex gap-2">
          <Button variant="outline" type="button" onClick={addEntry}>
            Add row
          </Button>
          <Button
            variant="ghost"
            type="button"
            onClick={handleReset}
            disabled={!isDirty || isSaving}
          >
            Reset
          </Button>
          <Button type="button" onClick={handleSave} disabled={!isDirty || isSaving}>
            {isSaving ? 'Saving…' : 'Save metadata'}
          </Button>
        </div>
      </div>
      <div className="space-y-3">
        {entries.length === 0 ? (
          <p className="text-sm text-foreground/60">No overrides yet. Add a row to store plan hints.</p>
        ) : (
          entries.map((entry) => (
            <div
              key={entry.id}
              className="grid gap-3 rounded-xl border border-white/10 bg-white/5 p-4 lg:grid-cols-12"
            >
              <div className="lg:col-span-4">
                <p className="text-xs font-medium uppercase tracking-wide text-foreground/60">Key</p>
                <Input
                  value={entry.key}
                  placeholder="plan_code"
                  className="mt-1"
                  onChange={(event) => updateEntry(entry.id, 'key', event.target.value)}
                />
              </div>
              <div className="lg:col-span-7">
                <p className="text-xs font-medium uppercase tracking-wide text-foreground/60">Value</p>
                <Input
                  value={entry.value}
                  placeholder="enterprise"
                  className="mt-1"
                  onChange={(event) => updateEntry(entry.id, 'value', event.target.value)}
                />
              </div>
              <div className="flex items-end justify-end lg:col-span-1">
                <Button type="button" variant="ghost" size="sm" onClick={() => removeEntry(entry.id)}>
                  Remove
                </Button>
              </div>
            </div>
          ))
        )}
      </div>
    </GlassPanel>
  );
}
