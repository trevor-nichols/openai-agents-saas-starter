import type { ChatMessage } from '../types';

export type MessagesAction =
  | { type: 'reset' }
  | { type: 'setAll'; messages: ChatMessage[] }
  | { type: 'append'; message: ChatMessage }
  | { type: 'insertAfterId'; anchorId: string; message: ChatMessage }
  | { type: 'insertBeforeId'; anchorId: string; message: ChatMessage }
  | { type: 'updateById'; id: string; patch: Partial<ChatMessage> }
  | { type: 'removeById'; id: string }
  | { type: 'batch'; actions: MessagesAction[] };

export function messagesReducer(state: ChatMessage[], action: MessagesAction): ChatMessage[] {
  switch (action.type) {
    case 'reset':
      return [];
    case 'setAll':
      return [...action.messages];
    case 'append':
      return [...state, action.message];
    case 'insertAfterId': {
      const anchorIndex = state.findIndex((msg) => msg.id === action.anchorId);
      if (anchorIndex === -1) return [...state, action.message];
      return [
        ...state.slice(0, anchorIndex + 1),
        action.message,
        ...state.slice(anchorIndex + 1),
      ];
    }
    case 'insertBeforeId': {
      const anchorIndex = state.findIndex((msg) => msg.id === action.anchorId);
      if (anchorIndex === -1) return [...state, action.message];
      return [
        ...state.slice(0, anchorIndex),
        action.message,
        ...state.slice(anchorIndex),
      ];
    }
    case 'updateById':
      return state.map((msg) => (msg.id === action.id ? { ...msg, ...action.patch } : msg));
    case 'removeById':
      return state.filter((msg) => msg.id !== action.id);
    case 'batch':
      return action.actions.reduce(messagesReducer, state);
    default:
      return state;
  }
}
