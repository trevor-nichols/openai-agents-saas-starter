export type TextParts = Map<number, string>;

export function assembledText(parts: TextParts | undefined): string {
  if (!parts || parts.size === 0) return '';
  return Array.from(parts.entries())
    .sort(([a], [b]) => a - b)
    .map(([, value]) => value)
    .join('');
}

export function appendDelta(
  store: Map<string, TextParts>,
  update: { itemId: string; contentIndex: number; delta: string },
): string {
  const { itemId, contentIndex, delta } = update;
  const parts = store.get(itemId) ?? new Map<number, string>();
  const existing = parts.get(contentIndex) ?? '';
  parts.set(contentIndex, `${existing}${delta}`);
  store.set(itemId, parts);
  return assembledText(parts);
}

export function replaceText(
  store: Map<string, TextParts>,
  update: { itemId: string; contentIndex: number; text: string },
): string {
  const { itemId, contentIndex, text } = update;
  const parts = store.get(itemId) ?? new Map<number, string>();
  parts.set(contentIndex, text);
  store.set(itemId, parts);
  return assembledText(parts);
}

