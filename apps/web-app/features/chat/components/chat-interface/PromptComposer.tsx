import { FormEvent } from 'react';
import type { ChatStatus } from 'ai';
import { Settings2Icon, TrashIcon } from 'lucide-react';

import {
  PromptInput,
  PromptInputButton,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputToolbar,
  PromptInputTools,
} from '@/components/ui/ai/prompt-input';
import { Loader } from '@/components/ui/ai/loader';
import { LocationOptIn } from '@/components/ui/location';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import type { ConversationLifecycleStatus } from '@/lib/chat/types';

type MemoryModeOption = 'inherit' | 'none' | 'trim' | 'summarize' | 'compact';

interface PromptComposerProps {
  messageInput: string;
  onChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => Promise<void> | void;
  onClearConversation?: () => void;
  isClearingConversation: boolean;
  isLoadingHistory: boolean;
  isSending: boolean;
  chatStatus?: ChatStatus;
  lifecycleStatus?: ConversationLifecycleStatus;
  activeAgent?: string;
  currentConversationId: string | null;
  shareLocation: boolean;
  onShareLocationChange: (value: boolean) => void;
  locationHint: {
    city?: string | null;
    region?: string | null;
    country?: string | null;
    timezone?: string | null;
  };
  onLocationHintChange: (
    field: 'city' | 'region' | 'country' | 'timezone',
    value: string
  ) => void;
  memoryMode: MemoryModeOption;
  memoryInjection?: boolean;
  onMemoryModeChange: (mode: MemoryModeOption) => void;
  onMemoryInjectionChange: (value: boolean) => void;
  isUpdatingMemory: boolean;
}

export function PromptComposer({
  messageInput,
  onChange,
  onSubmit,
  onClearConversation,
  isClearingConversation,
  isLoadingHistory,
  isSending,
  chatStatus,
  activeAgent,
  currentConversationId,
  shareLocation,
  onShareLocationChange,
  locationHint,
  onLocationHintChange,
  memoryMode,
  memoryInjection,
  onMemoryModeChange,
  onMemoryInjectionChange,
  isUpdatingMemory,
}: PromptComposerProps) {
  const disabled = isSending || isLoadingHistory;
  const memoryDisabled = disabled || !currentConversationId || isUpdatingMemory;

  return (
    <div className="mx-auto w-full max-w-3xl px-4 pb-4">
      <PromptInput
        onSubmit={onSubmit}
        className="divide-y-0 overflow-hidden rounded-xl border bg-background shadow-lg transition-all focus-within:ring-1 focus-within:ring-ring"
      >
        <PromptInputTextarea
          value={messageInput}
          onChange={(event) => onChange(event.target.value)}
          placeholder={
            currentConversationId
              ? `Message ${currentConversationId.substring(0, 8)}…`
              : 'Ask your agent…'
          }
          disabled={disabled}
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
                >
                  <Settings2Icon className="size-4" />
                  <span className="sr-only">Chat settings</span>
                </PromptInputButton>
              </PopoverTrigger>
              <PopoverContent className="w-80 p-4" align="start">
                <div className="grid gap-4">
                  <div className="space-y-2">
                    <h4 className="font-medium text-sm leading-none">
                      Chat Configuration
                    </h4>
                    <p className="text-muted-foreground text-xs">
                      Manage memory and context settings for this session.
                    </p>
                  </div>
                  <Separator />
                  <div className="grid gap-2">
                    <Label htmlFor="memory-mode" className="text-xs">
                      Memory Strategy
                    </Label>
                    <Select
                      value={memoryMode}
                      onValueChange={(value) =>
                        onMemoryModeChange(value as MemoryModeOption)
                      }
                      disabled={memoryDisabled}
                    >
                      <SelectTrigger
                        id="memory-mode"
                        className="h-8 w-full text-xs"
                      >
                        <SelectValue placeholder="Select strategy" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="inherit">Use defaults</SelectItem>
                        <SelectItem value="none">None</SelectItem>
                        <SelectItem value="trim">Trim</SelectItem>
                        <SelectItem value="summarize">Summarize</SelectItem>
                        <SelectItem value="compact">Compact</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex items-center justify-between gap-2">
                    <Label
                      htmlFor="memory-injection"
                      className="text-xs font-normal"
                    >
                      Inject summary
                    </Label>
                    <Switch
                      id="memory-injection"
                      className="scale-75"
                      checked={Boolean(memoryInjection)}
                      disabled={memoryDisabled}
                      onCheckedChange={(checked) =>
                        onMemoryInjectionChange(checked)
                      }
                    />
                  </div>
                  <Separator />
                  <div className="space-y-2">
                    <Label className="text-xs">Location Context</Label>
                    <LocationOptIn
                      shareLocation={shareLocation}
                      onShareLocationChange={onShareLocationChange}
                      location={locationHint}
                      onLocationChange={onLocationHintChange}
                      disabled={disabled}
                    />
                  </div>
                </div>
              </PopoverContent>
            </Popover>

            {onClearConversation && currentConversationId ? (
              <PromptInputButton
                variant="ghost"
                size="icon"
                className="size-8 text-muted-foreground hover:text-destructive"
                onClick={() => {
                  void onClearConversation();
                }}
                disabled={isClearingConversation || isLoadingHistory}
                title="Clear conversation"
              >
                <TrashIcon className="size-4" />
                <span className="sr-only">Clear chat</span>
              </PromptInputButton>
            ) : null}
          </PromptInputTools>

          <div className="flex items-center gap-2">
            {chatStatus === 'streaming' ? (
              <div className="flex items-center gap-1.5 rounded-full bg-muted/50 px-2 py-0.5 text-xs text-muted-foreground">
                <Loader size={12} />
                <span className="uppercase tracking-wider text-[10px] font-medium">
                  Generating
                </span>
              </div>
            ) : null}

            {activeAgent ? (
              <span className="hidden text-[10px] text-muted-foreground uppercase tracking-wider font-medium sm:block">
                {activeAgent}
              </span>
            ) : null}

            <PromptInputSubmit
              status={chatStatus}
              disabled={disabled || !messageInput.trim()}
              className="size-8 rounded-xl transition-all shadow-sm"
            />
          </div>
        </PromptInputToolbar>
      </PromptInput>
      <p className="mt-2 text-center text-[10px] text-muted-foreground/60">
        AI can make mistakes. Please verify important information.
      </p>
    </div>
  );
}
