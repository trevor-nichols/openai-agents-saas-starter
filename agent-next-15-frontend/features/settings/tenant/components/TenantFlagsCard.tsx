'use client';

import { useEffect, useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { GlassPanel, SectionHeader } from '@/components/ui/foundation';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { useToast } from '@/components/ui/use-toast';

import { FLAG_PRESETS } from '../constants';

interface TenantFlagsCardProps {
  flags: Record<string, boolean>;
  isSaving: boolean;
  onSubmit: (flags: Record<string, boolean>) => Promise<void>;
}

export function TenantFlagsCard({ flags, isSaving, onSubmit }: TenantFlagsCardProps) {
  const toast = useToast();
  const [flagState, setFlagState] = useState<Record<string, boolean>>(flags);
  const [customKey, setCustomKey] = useState('');

  useEffect(() => {
    setFlagState(flags);
  }, [flags]);

  const presetLookup = useMemo(() => new Set<string>(FLAG_PRESETS.map((preset) => preset.key)), []);
  const customFlags = Object.keys(flagState).filter((key) => !presetLookup.has(key));

  const toggleFlag = (key: string, value: boolean) => {
    setFlagState((prev) => ({ ...prev, [key]: value }));
  };

  const removeFlag = (key: string) => {
    setFlagState((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
  };

  const handleSave = async () => {
    try {
      await onSubmit(flagState);
      toast.success({
        title: 'Flags updated',
        description: 'Tenant feature toggles saved.',
      });
    } catch (error) {
      toast.error({
        title: 'Unable to update flags',
        description: error instanceof Error ? error.message : 'Try again shortly.',
      });
    }
  };

  const handleAddCustomFlag = () => {
    const trimmed = customKey.trim();
    if (!trimmed) {
      toast.error({ title: 'Flag key is required', description: 'Provide a unique identifier.' });
      return;
    }
    if (Object.hasOwn(flagState, trimmed)) {
      toast.error({ title: 'Flag already exists', description: 'Use a new identifier.' });
      return;
    }
    setFlagState((prev) => ({ ...prev, [trimmed]: true }));
    setCustomKey('');
  };

  const hasChanges = useMemo(() => {
    return JSON.stringify(flagState) !== JSON.stringify(flags);
  }, [flagState, flags]);

  return (
    <GlassPanel className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <SectionHeader
          eyebrow="Feature flags"
          title="Tenant feature toggles"
          description="Enable betas, enforce security policies, or configure sandboxes."
        />
        <Button type="button" onClick={handleSave} disabled={!hasChanges || isSaving}>
          {isSaving ? 'Saving…' : 'Save flags'}
        </Button>
      </div>

      <div className="space-y-3">
        {FLAG_PRESETS.map((preset) => (
          <div
            key={preset.key}
            className="flex flex-col gap-2 rounded-xl border border-white/10 bg-white/5 p-4 sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <p className="font-medium text-foreground">{preset.label}</p>
              <p className="text-sm text-foreground/60">{preset.description}</p>
            </div>
            <Switch
              checked={Boolean(flagState[preset.key])}
              onCheckedChange={(value) => toggleFlag(preset.key, value)}
            />
          </div>
        ))}
      </div>

      <div className="space-y-3">
        <p className="text-sm font-semibold uppercase tracking-wide text-foreground/60">Custom flags</p>
        {customFlags.length === 0 ? (
          <p className="text-sm text-foreground/60">No custom flags yet.</p>
        ) : (
          customFlags.map((key) => (
            <div
              key={key}
              className="flex flex-col gap-3 rounded-xl border border-white/10 bg-white/5 p-4 sm:flex-row sm:items-center sm:justify-between"
            >
              <div>
                <p className="font-medium text-foreground">{key}</p>
                <p className="text-xs text-foreground/60">Custom flag</p>
              </div>
              <div className="flex items-center gap-3">
                <Switch
                  checked={Boolean(flagState[key])}
                  onCheckedChange={(value) => toggleFlag(key, value)}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeFlag(key)}
                  disabled={isSaving}
                >
                  Remove
                </Button>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="rounded-xl border border-dashed border-white/20 p-4">
        <p className="text-sm font-medium text-foreground">Add custom flag</p>
        <div className="mt-3 flex flex-col gap-2 sm:flex-row">
          <Input
            value={customKey}
            placeholder="flag_key"
            onChange={(event) => setCustomKey(event.target.value)}
          />
          <Button type="button" variant="outline" onClick={handleAddCustomFlag} disabled={isSaving}>
            Add flag
          </Button>
        </div>
      </div>
    </GlassPanel>
  );
}
