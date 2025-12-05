import { CodeBlock } from './code-block';
import { FileSearchResults } from './file-search-results';
import { Image } from './image';
import type { FileSearchResult, ImageGenerationCall } from '@/lib/api/client/types.gen';

/**
 * Shared renderer for tool outputs across chat + workflow surfaces.
 */
export type ToolLike = {
  output?: unknown;
  label?: string | null;
};

const isFileSearchResults = (output: unknown): output is FileSearchResult[] =>
  Array.isArray(output) &&
  output.every(
    (item) =>
      typeof item === 'object' &&
      item !== null &&
      'file_id' in (item as Record<string, unknown>),
  );

const isImageGenerationCall = (value: unknown): value is ImageGenerationCall =>
  typeof value === 'object' &&
  value !== null &&
  'type' in value &&
  (value as { type?: string }).type === 'image_generation_call';

const isCodeInterpreterOutput = (
  output: unknown,
): output is {
  outputs?: unknown;
  container_id?: string | null;
  container_mode?: string | null;
  annotations?: unknown;
  [key: string]: unknown;
} => typeof output === 'object' && output !== null && 'outputs' in (output as Record<string, unknown>);

export function renderToolOutput(tool: ToolLike) {
  if (!tool.output) return undefined;

  if (isFileSearchResults(tool.output)) {
    return <FileSearchResults results={tool.output} />;
  }

  if (Array.isArray(tool.output) && tool.output.length && isImageGenerationCall(tool.output[0])) {
    return <Image frames={tool.output as ImageGenerationCall[]} className="max-w-xl" alt="Generated image" />;
  }

  if (isImageGenerationCall(tool.output)) {
    return <Image frames={[tool.output]} className="max-w-xl" alt="Generated image" />;
  }

  if (isCodeInterpreterOutput(tool.output)) {
    const { outputs, container_id, container_mode, annotations, ...rest } = tool.output;
    return (
      <div className="space-y-2">
        {(container_id || container_mode) && (
          <div className="flex items-center gap-2 text-xs text-foreground/70">
            {container_id ? <span>Container: {container_id}</span> : null}
            {container_mode ? <span>• Mode: {container_mode}</span> : null}
          </div>
        )}
        {annotations ? (
          <div className="text-[11px] text-foreground/60">Annotations: {JSON.stringify(annotations)}</div>
        ) : null}
        <CodeBlock code={JSON.stringify({ outputs, ...rest }, null, 2)} language="json" />
      </div>
    );
  }

  return <CodeBlock code={JSON.stringify(tool.output, null, 2)} language="json" />;
}
