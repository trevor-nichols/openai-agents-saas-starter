import type { MutableRefObject } from 'react';

export type AssistantTurnMessage = { itemId: string; uiId: string; outputIndex: number };

export interface TurnRuntimeRefs {
  lastActiveAgentRef: MutableRefObject<string>;
  lastResponseIdRef: MutableRefObject<string | null>;
  turnUserMessageIdRef: MutableRefObject<string | null>;
  assistantIdNonceRef: MutableRefObject<number>;
  messageItemToUiIdRef: MutableRefObject<Map<string, string>>;
  assistantTurnMessagesRef: MutableRefObject<AssistantTurnMessage[]>;
  lastAssistantMessageUiIdRef: MutableRefObject<string | null>;
  latestAssistantTextByUiIdRef: MutableRefObject<Map<string, string>>;
}

export function resetTurnRuntimeRefs(refs: TurnRuntimeRefs) {
  refs.turnUserMessageIdRef.current = null;
  refs.messageItemToUiIdRef.current = new Map();
  refs.assistantTurnMessagesRef.current = [];
  refs.lastAssistantMessageUiIdRef.current = null;
  refs.latestAssistantTextByUiIdRef.current = new Map();
}

export function resetViewRuntimeRefs(refs: TurnRuntimeRefs, selectedAgent: string) {
  refs.lastActiveAgentRef.current = selectedAgent;
  refs.lastResponseIdRef.current = null;
  resetTurnRuntimeRefs(refs);
}

export function beginTurnRuntime(refs: TurnRuntimeRefs, userMessageId: string) {
  refs.turnUserMessageIdRef.current = userMessageId;
  refs.messageItemToUiIdRef.current = new Map();
  refs.assistantTurnMessagesRef.current = [];
  refs.lastAssistantMessageUiIdRef.current = null;
  refs.latestAssistantTextByUiIdRef.current = new Map();
}

