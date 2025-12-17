import type { Annotation } from '@/lib/chat/types';
import type { PublicSseEvent } from '@/lib/api/client/types.gen';

export type CitationsState = {
  byItemId: Map<string, Annotation[]>;
};

export function createCitationsState(): CitationsState {
  return { byItemId: new Map() };
}

export function applyCitationEvent(state: CitationsState, event: PublicSseEvent): void {
  if (event.kind !== 'message.citation') return;
  const existing = state.byItemId.get(event.item_id) ?? [];
  state.byItemId.set(event.item_id, [...existing, event.citation as Annotation]);
}

export function getCitationsForItem(state: CitationsState, itemId: string): Annotation[] | null {
  const citations = state.byItemId.get(itemId);
  return citations?.length ? citations : null;
}

