import { FormEvent, useEffect, useRef, useState } from 'react';

import { Label } from '@/components/ui/label';
import { SkeletonPanel, EmptyState } from '@/components/ui/states';
import { InlineTag } from '@/components/ui/foundation';
import { LocationOptIn } from '@/components/ui/location';
import type { LocationHint } from '@/lib/api/client/types.gen';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import {
  PromptInput,
  PromptInputButton,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputToolbar,
  PromptInputTools,
} from '@/components/ui/ai/prompt-input';
import { Loader } from '@/components/ui/ai/loader';
import { Settings2Icon, TrashIcon } from 'lucide-react';

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
    return (
      <EmptyState
        title="Select a workflow"
        description="Choose a workflow to view details and run it."
      />
    );
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (isRunning || !message.trim()) return;
    await onRun({
      workflowKey: selectedKey,
      message,
      shareLocation,
      location: shareLocation ? location : null,
    });
  };

  return (
    <div className="space-y-4">
      <PromptInput onSubmit={handleSubmit} variant="composer">
        <Label htmlFor="workflow-message" className="sr-only">
          Message
        </Label>
        <PromptInputTextarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          id="workflow-message"
          placeholder="Ask the workflow to act..."
          disabled={isRunning}
          ref={textareaRef}
          minHeight={52}
        />
        <PromptInputToolbar className="justify-between px-3 pb-3 pt-2">
          <PromptInputTools>
            <Popover>
              <PopoverTrigger asChild>
                <PromptInputButton
                  variant="ghost"
                  size="icon"
                  className="size-8 text-muted-foreground hover:text-foreground"
                  disabled={isRunning}
                >
                  <Settings2Icon className="size-4" />
                  <span className="sr-only">Workflow run options</span>
                </PromptInputButton>
              </PopoverTrigger>
              <PopoverContent className="w-96 p-4" align="start">
                <div className="space-y-3">
                  <div className="space-y-1">
                    <h4 className="text-sm font-medium leading-none">
                      Run options
                    </h4>
                    <p className="text-xs text-muted-foreground">
                      Optional context sent along with your workflow input.
                    </p>
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
                </div>
              </PopoverContent>
            </Popover>

            <PromptInputButton
              variant="ghost"
              size="icon"
              className="size-8 text-muted-foreground hover:text-destructive"
              onClick={() => setMessage('')}
              disabled={isRunning || !message}
              title="Clear message"
            >
              <TrashIcon className="size-4" />
              <span className="sr-only">Clear message</span>
            </PromptInputButton>
          </PromptInputTools>

          <div className="flex items-center gap-2">
            {streamStatus === 'connecting' || streamStatus === 'streaming' ? (
              <div className="flex items-center gap-1.5 rounded-full bg-muted/50 px-2 py-0.5 text-xs text-muted-foreground">
                <Loader size={12} />
                <span className="uppercase tracking-wider text-[10px] font-medium">
                  Running
                </span>
              </div>
            ) : null}

            <InlineTag tone={streamStatus === 'error' ? 'warning' : 'default'}>
              {streamStatus}
            </InlineTag>

            <PromptInputSubmit
              size="sm"
              disabled={isRunning || !message.trim()}
              className="h-8 rounded-xl transition-all shadow-sm"
            >
              {isRunning ? 'Running…' : 'Run workflow'}
            </PromptInputSubmit>
          </div>
        </PromptInputToolbar>
      </PromptInput>

      {runError ? (
        <div className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {runError}
        </div>
      ) : null}

      {/* Stream rendering lives in WorkflowStreamLog within the parent workspace. */}
    </div>
  );
}
