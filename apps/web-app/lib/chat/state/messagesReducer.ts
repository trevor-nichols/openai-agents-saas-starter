import type { ChatMessage } from '../types';

export type MessagesAction =
  | { type: 'reset' }
  | { type: 'setAll'; messages: ChatMessage[] }
  | { type: 'append'; message: ChatMessage }
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
