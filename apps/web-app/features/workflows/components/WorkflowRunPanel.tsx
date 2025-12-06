import { useEffect, useRef, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { SkeletonPanel, EmptyState } from '@/components/ui/states';
import { InlineTag } from '@/components/ui/foundation';
import { LocationOptIn } from '@/components/ui/location';
import type { LocationHint } from '@/lib/api/client/types.gen';

interface WorkflowRunPanelProps {
  selectedKey: string | null;
  onRun: (payload: {
    workflowKey: string;
    message: string;
    shareLocation?: boolean;
    location?: LocationHint | null;
  }) => Promise<void>;
  isRunning: boolean;
  runError?: string | null;
  isLoadingWorkflows?: boolean;
  streamStatus?: 'idle' | 'connecting' | 'streaming' | 'completed' | 'error';
}

export function WorkflowRunPanel({
  selectedKey,
  onRun,
  isRunning,
  runError,
  isLoadingWorkflows,
  streamStatus = 'idle',
}: WorkflowRunPanelProps) {
  const [message, setMessage] = useState('');
  const [shareLocation, setShareLocation] = useState(false);
  const [location, setLocation] = useState<LocationHint>({
    city: '',
    region: '',
    country: '',
    timezone: '',
  });
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [selectedKey]);

  if (isLoadingWorkflows) {
    return <SkeletonPanel lines={6} />;
  }

  if (!selectedKey) {
    return <EmptyState title="Select a workflow" description="Choose a workflow to view details and run it." />;
  }

  const handleSubmit = async () => {
    if (!message.trim()) return;
    await onRun({
      workflowKey: selectedKey,
      message,
      shareLocation,
      location: shareLocation ? location : null,
    });
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label className="text-sm font-semibold">Message</Label>
        <Textarea
          rows={3}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Ask the workflow to act..."
          disabled={isRunning}
          ref={textareaRef}
        />
      </div>
      <LocationOptIn
        id="workflow-share-location"
        shareLocation={shareLocation}
        onShareLocationChange={setShareLocation}
        location={location}
        onLocationChange={(field, value) =>
          setLocation((prev) => ({
            ...prev,
            [field]: value,
          }))
        }
        disabled={isRunning}
        label="Share location with hosted tools"
        showOptionalBadge
      />
      <div className="flex gap-2 items-center">
        <Button onClick={handleSubmit} disabled={isRunning || !message.trim()}>
          {isRunning ? 'Running…' : 'Run workflow'}
        </Button>
        <Button variant="ghost" onClick={() => setMessage('')} disabled={isRunning}>
          Clear
        </Button>
        <InlineTag tone={streamStatus === 'error' ? 'warning' : 'default'}>
          {streamStatus}
        </InlineTag>
      </div>

      {runError ? (
        <div className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {runError}
        </div>
      ) : null}

      {/* Stream rendering lives in WorkflowStreamLog within the parent workspace. */}
    </div>
  );
}
