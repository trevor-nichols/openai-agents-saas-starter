import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { SkeletonPanel, EmptyState } from '@/components/ui/states';
import { Switch } from '@/components/ui/switch';

interface WorkflowRunPanelProps {
  selectedKey: string | null;
  onRun: (payload: { workflowKey: string; message: string; conversationId?: string | null; shareLocation?: boolean }) => Promise<void>;
  isRunning: boolean;
  runError?: string | null;
  isLoadingWorkflows?: boolean;
}

export function WorkflowRunPanel({
  selectedKey,
  onRun,
  isRunning,
  runError,
  isLoadingWorkflows,
}: WorkflowRunPanelProps) {
  const [message, setMessage] = useState('');
  const [conversationId, setConversationId] = useState('');
  const [shareLocation, setShareLocation] = useState(false);

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
      conversationId: conversationId.trim() || null,
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
        />
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <div className="space-y-1">
          <Label className="text-sm font-semibold">Conversation ID (optional)</Label>
          <Input
            value={conversationId}
            onChange={(e) => setConversationId(e.target.value)}
            placeholder="Reuse an existing conversation"
            disabled={isRunning}
          />
        </div>
        <div className="flex items-center gap-3">
          <Switch
            id="workflow-share-location"
            checked={shareLocation}
            onCheckedChange={setShareLocation}
            disabled={isRunning}
          />
          <Label htmlFor="workflow-share-location" className="text-sm">
            Share location with hosted tools
          </Label>
        </div>
      </div>
      <div className="flex gap-2">
        <Button onClick={handleSubmit} disabled={isRunning || !message.trim()}>
          {isRunning ? 'Running…' : 'Run workflow'}
        </Button>
        <Button variant="ghost" onClick={() => setMessage('')} disabled={isRunning}>
          Clear
        </Button>
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
