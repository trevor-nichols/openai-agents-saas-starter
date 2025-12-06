import { Plus, Search, History } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface ConversationSidebarHeaderProps {
  searchTerm: string;
  onSearchChange: (value: string) => void;
  onNewConversation: () => void;
}

export function ConversationSidebarHeader({ searchTerm, onSearchChange, onNewConversation }: ConversationSidebarHeaderProps) {
  return (
    <div className="flex flex-col gap-4 p-4 pb-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-muted-foreground">
          <History className="h-4 w-4" />
          <h2 className="text-sm font-medium">History</h2>
        </div>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                onClick={onNewConversation}
                size="icon"
                variant="ghost"
                className="h-8 w-8 rounded-full hover:bg-primary/10 hover:text-primary"
              >
                <Plus className="h-4 w-4" />
                <span className="sr-only">New Chat</span>
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom">New Conversation</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground/50" />
        <Input
          placeholder="Search chats..."
          value={searchTerm}
          onChange={(event) => onSearchChange(event.target.value)}
          className="h-9 rounded-lg border-transparent bg-muted/50 pl-9 text-sm focus-visible:bg-background focus-visible:ring-1"
        />
      </div>
    </div>
  );
}
