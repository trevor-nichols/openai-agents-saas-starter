export type ChunkTarget = {
  entity_kind: string;
  entity_id: string;
  field: string;
  part_index?: number | null;
};

export type ChunkKey = string;

export function chunkKeyFor(target: ChunkTarget): ChunkKey {
  return `${target.entity_kind}:${target.entity_id}:${target.field}:${target.part_index ?? ''}`;
}

export type ChunkAccumulator = {
  encoding: 'base64' | 'utf8' | undefined;
  parts: Map<number, string>;
};

export function applyChunkDelta(
  chunksByTarget: Map<ChunkKey, ChunkAccumulator>,
  update: { target: ChunkTarget; encoding: 'base64' | 'utf8' | undefined; chunkIndex: number; data: string },
): void {
  const key = chunkKeyFor(update.target);
  const existing = chunksByTarget.get(key) ?? {
    encoding: update.encoding,
    parts: new Map<number, string>(),
  };
  if (!existing.encoding) existing.encoding = update.encoding;
  existing.parts.set(update.chunkIndex, update.data);
  chunksByTarget.set(key, existing);
}

export function takeChunk(
  chunksByTarget: Map<ChunkKey, ChunkAccumulator>,
  target: ChunkTarget,
): { encoding: 'base64' | 'utf8' | undefined; data: string } | null {
  const key = chunkKeyFor(target);
  const acc = chunksByTarget.get(key);
  if (!acc) return null;
  chunksByTarget.delete(key);

  const assembled = Array.from(acc.parts.entries())
    .sort(([a], [b]) => a - b)
    .map(([, value]) => value)
    .join('');

  return { encoding: acc.encoding, data: assembled };
}

export function mimeFromImageFormat(format: string | null | undefined): string {
  if (!format) return 'image/png';
  const normalized = format.toLowerCase();
  if (normalized.includes('png')) return 'image/png';
  if (normalized.includes('jpg') || normalized.includes('jpeg')) return 'image/jpeg';
  if (normalized.includes('webp')) return 'image/webp';
  return `image/${normalized}`;
}

export function asDataUrlOrRawText(params: {
  encoding: 'base64' | 'utf8' | undefined;
  data: string;
  mimeType?: string | null;
}): string {
  if (params.encoding === 'base64' && params.mimeType) {
    return `data:${params.mimeType};base64,${params.data}`;
  }
  return params.data;
}

