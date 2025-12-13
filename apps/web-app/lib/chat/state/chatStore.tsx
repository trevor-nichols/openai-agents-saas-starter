import { useEffect, useState, createContext, useContext, useCallback, useSyncExternalStore, ReactNode, memo } from 'react';
import type { UseChatControllerReturn } from '../controller/useChatController';
import type { ChatMessage, ToolEventAnchors, ToolState } from '../types';

// shallow equality for objects/arrays
function shallowEqual<T>(a: T, b: T) {
  if (Object.is(a, b)) return true;
  if (!a || !b) return false;
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i += 1) {
      if (!Object.is(a[i], b[i])) return false;
    }
    return true;
  }
  if (typeof a === 'object' && typeof b === 'object') {
    const aKeys = Object.keys(a as Record<string, unknown>);
    const bKeys = Object.keys(b as Record<string, unknown>);
    if (aKeys.length !== bKeys.length) return false;
    for (const k of aKeys) {
      if (!Object.prototype.hasOwnProperty.call(b, k) || !Object.is((a as any)[k], (b as any)[k])) {
        return false;
      }
    }
    return true;
  }
  return false;
}

class ChatStore {
  private state: UseChatControllerReturn;
  private listeners = new Set<() => void>();

  constructor(initial: UseChatControllerReturn) {
    this.state = initial;
  }

  getState = () => this.state;

  subscribe = (listener: () => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  setState(next: UseChatControllerReturn) {
    if (next === this.state) return;
    this.state = next;
    this.listeners.forEach((listener) => listener());
  }
}

const ChatStoreContext = createContext<ChatStore | null>(null);

export function ChatControllerProvider({ value, children }: { value: UseChatControllerReturn; children: ReactNode }) {
  const [store] = useState(() => new ChatStore(value));

  useEffect(() => {
    store.setState(value);
  }, [store, value]);

  return <ChatStoreContext.Provider value={store}>{children}</ChatStoreContext.Provider>;
}

function useChatStore() {
  const store = useContext(ChatStoreContext);
  if (!store) throw new Error('useChatSelector must be used within ChatControllerProvider');
  return store;
}

export function useChatSelector<T>(
  selector: (state: UseChatControllerReturn) => T,
  equalityFn: (a: T, b: T) => boolean = shallowEqual,
) {
  const store = useChatStore();

  const getSnapshot = useCallback(() => selector(store.getState()), [store, selector]);

  const subscribe = useCallback(
    (notify: () => void) => {
      let current = selector(store.getState());
      return store.subscribe(() => {
        const next = selector(store.getState());
        if (!equalityFn(current, next)) {
          current = next;
          notify();
        }
      });
    },
    [store, selector, equalityFn],
  );

  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}

export const useChatMessages = () => useChatSelector((s) => s.messages);
export const useChatToolEvents = () => useChatSelector((s) => s.toolEvents, shallowEqual);
export const useChatToolEventAnchors = () => useChatSelector((s) => s.toolEventAnchors, shallowEqual);
export const useChatGuardrailEvents = () => useChatSelector((s) => s.guardrailEvents, shallowEqual);
export const useChatLifecycle = () => useChatSelector((s) => s.lifecycleStatus);
export const useChatAgentNotices = () => useChatSelector((s) => s.agentNotices, shallowEqual);

// Small memo helper for components that consume selectors with no props
export const memoSelector = <P extends object>(component: React.FC<P>) => memo(component);

// Explicit exports to aid tree-shaking in consumers
export type { ChatMessage, ToolEventAnchors, ToolState };
