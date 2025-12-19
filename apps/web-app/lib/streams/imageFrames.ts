export type GeneratedImageStatus =
  | 'in_progress'
  | 'generating'
  | 'partial_image'
  | 'completed';

export type GeneratedImageFrame = {
  id: string;
  src: string;
  status: GeneratedImageStatus;
  outputIndex?: number;
  revisedPrompt?: string;
};

const STATUS_SET: ReadonlySet<string> = new Set([
  'in_progress',
  'generating',
  'partial_image',
  'completed',
]);

export function isGeneratedImageFrame(value: unknown): value is GeneratedImageFrame {
  if (!value || typeof value !== 'object') return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record.id === 'string' &&
    typeof record.src === 'string' &&
    typeof record.status === 'string' &&
    STATUS_SET.has(record.status)
  );
}

export function isGeneratedImageFrames(value: unknown): value is GeneratedImageFrame[] {
  return Array.isArray(value) && value.every(isGeneratedImageFrame);
}

