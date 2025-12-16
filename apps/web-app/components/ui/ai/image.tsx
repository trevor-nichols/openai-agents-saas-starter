import { cn } from '@/lib/utils';
import type { Experimental_GeneratedImage } from 'ai';
import type { GeneratedImageFrame, GeneratedImageStatus } from '@/lib/streams/imageFrames';

type BaseImageProps = Partial<Experimental_GeneratedImage> & {
  className?: string;
  alt?: string;
};

export type ImageProps = BaseImageProps & {
  /**
   * Optional stream of image generation events (partial frames + final).
   * When provided, frames take precedence over the single `base64` image.
   */
  frames?: GeneratedImageFrame[];
};

type EnrichedFrame = {
  key: string;
  src: string;
  status: GeneratedImageStatus;
  label: string;
  outputIndex: number | undefined;
  revisedPrompt: string | undefined;
};

const statusLabel: Record<GeneratedImageStatus, string> = {
  in_progress: 'Starting',
  generating: 'Generating',
  partial_image: 'Preview',
  completed: 'Completed',
};

/**
 * Renders a generated image, optionally showing progressive frames from
 * streamed image frames (partial images + final output) in a single view.
 */
export const Image = ({
  frames,
  base64,
  mediaType = 'image/png',
  className,
  alt,
  uint8Array: _uint8Array,
  ...rest
}: ImageProps) => {
  const enrichedFrames: EnrichedFrame[] =
    frames
      ?.map((frame, index) => {
        if (!frame.src) return null;
        return {
          key: frame.id ?? `${frame.outputIndex ?? index}-${frame.status}-${index}`,
          src: frame.src,
          status: frame.status,
          label: statusLabel[frame.status] ?? frame.status,
          outputIndex: frame.outputIndex ?? undefined,
          revisedPrompt: frame.revisedPrompt ?? undefined,
        };
      })
      .filter((frame): frame is EnrichedFrame => Boolean(frame)) ?? [];

  const primaryFrame =
    enrichedFrames.find((frame) => frame.status === 'completed') ??
    enrichedFrames[enrichedFrames.length - 1];

  // Fallback to the legacy single-base64 rendering if no frames are provided.
  if (!primaryFrame) {
    const src = base64 ? `data:${mediaType};base64,${base64}` : undefined;
    return (
      // eslint-disable-next-line @next/next/no-img-element -- Using <img> for base64-encoded AI-generated images
      <img
        alt={alt}
        className={cn('h-auto max-w-full overflow-hidden rounded-md', className)}
        src={src}
        {...rest}
      />
    );
  }

  const timeline = enrichedFrames.length > 1 ? enrichedFrames : [];

  return (
    <div className={cn('space-y-3', className)}>
      <div className="relative w-full overflow-hidden rounded-lg border bg-white/5">
        {/* eslint-disable-next-line @next/next/no-img-element -- data/remote URLs are safe here */}
        <img
          src={primaryFrame.src}
          alt={alt}
          className="h-auto w-full max-h-[540px] object-contain bg-black/40"
          {...rest}
        />

        <div className="absolute left-2 top-2 flex items-center gap-2 rounded-full bg-black/60 px-3 py-1 text-xs text-white/90">
          <span className="font-semibold">{primaryFrame.label}</span>
          {typeof primaryFrame.outputIndex === 'number' ? (
            <span className="rounded-full bg-white/15 px-2 py-0.5">#{primaryFrame.outputIndex}</span>
          ) : null}
        </div>
        {primaryFrame.revisedPrompt ? (
          <div className="absolute inset-x-0 bottom-0 bg-black/55 px-3 py-2 text-xs text-white/85">
            {primaryFrame.revisedPrompt}
          </div>
        ) : null}
      </div>

      {timeline.length ? (
        <div className="grid grid-cols-[repeat(auto-fit,minmax(80px,1fr))] gap-2">
          {timeline.map((frame) => (
            <div
              key={frame.key}
              className="group overflow-hidden rounded-md border border-white/10 bg-white/5"
            >
              {/* eslint-disable-next-line @next/next/no-img-element -- data/remote URLs are safe here */}
              <img
                src={frame.src}
                alt={frame.label}
                className="aspect-square h-full w-full object-cover transition group-hover:scale-105"
              />
              <div className="flex items-center justify-between gap-2 px-2 py-1 text-[11px] text-foreground/70">
                <span className="truncate">{frame.label}</span>
                {typeof frame.outputIndex === 'number' ? <span>#{frame.outputIndex}</span> : null}
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
};
