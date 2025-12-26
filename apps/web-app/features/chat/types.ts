import type { ConversationListItem } from '@/types/conversations';
import type { AgentSummary } from '@/types/agents';
import type { ToolRegistry } from '@/types/tools';

export interface WorkspaceHeaderState {
  title: string;
  description: string;
  inlineTagTone: 'positive' | 'warning' | 'default';
  inlineTagText: string;
}

export interface AgentSwitcherProps {
  agents: AgentSummary[];
  selectedAgent: string;
  onChange: (value: string) => void;
}

export interface ToolDrawerState {
  isOpen: boolean;
  selectedAgentLabel: string;
}

export interface ToolMetadataPanelProps {
  selectedAgentKey: string;
  selectedAgentLabel?: string;
  tools: ToolRegistry;
  isLoading: boolean;
  error?: string | null;
  onRefresh: () => void;
}

export interface ConversationDrawerState {
  isOpen: boolean;
  conversationId: string | null;
}

export type SidebarConversation = ConversationListItem;
