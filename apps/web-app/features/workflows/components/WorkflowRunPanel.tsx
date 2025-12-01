import { useEffect, useRef, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { SkeletonPanel, EmptyState } from '@/components/ui/states';
import { Switch } from '@/components/ui/switch';
import { InlineTag } from '@/components/ui/foundation';

interface WorkflowRunPanelProps {
  selectedKey: string | null;
  onRun: (payload: { workflowKey: string; message: string; shareLocation?: boolean }) => Promise<void>;
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
      <div className="flex items-center gap-3">
        <Switch
          id="workflow-share-location"
          checked={shareLocation}
          onCheckedChange={setShareLocation}
          disabled={isRunning}
          aria-label="Share location with hosted tools"
        />
        <Label htmlFor="workflow-share-location" className="text-sm">
          Share location with hosted tools
        </Label>
      </div>
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
