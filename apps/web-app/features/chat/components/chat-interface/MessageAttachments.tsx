import { formatAttachmentSize } from '../../utils/formatters';
import type { AttachmentState } from '../../hooks/useAttachmentResolver';
import type { MessageAttachment } from '@/lib/api/client/types.gen';

interface MessageAttachmentsProps {
  attachments: MessageAttachment[];
  attachmentState: AttachmentState;
  onResolve: (objectId: string) => Promise<void>;
  isBusy: boolean;
}

export function MessageAttachments({ attachments, attachmentState, onResolve, isBusy }: MessageAttachmentsProps) {
  if (!attachments.length) return null;

  return (
    <div className="mt-3 space-y-2">
      <p className="text-xs font-semibold uppercase tracking-wide text-foreground/60">Attachments</p>
      <div className="space-y-2">
        {attachments.map((attachment) => {
          const state = attachmentState[attachment.object_id];
          const effectiveUrl = attachment.url ?? state?.url;

          return (
            <div
              key={attachment.object_id}
              className="flex items-center justify-between gap-3 rounded-md border border-white/5 bg-white/5 px-3 py-2 text-xs"
            >
              <div className="flex flex-col">
                <span className="font-medium text-foreground">{attachment.filename}</span>
                <span className="text-foreground/60">
                  {attachment.mime_type ?? 'file'}
                  {attachment.size_bytes ? ` • ${formatAttachmentSize(attachment.size_bytes)}` : ''}
                </span>
              </div>

              {effectiveUrl ? (
                <a className="text-primary font-semibold hover:underline" href={effectiveUrl} target="_blank" rel="noreferrer">
                  Download
                </a>
              ) : state?.loading ? (
                <span className="text-foreground/50">Fetching link…</span>
              ) : (
                <div className="flex flex-col items-end gap-1">
                  <button
                    type="button"
                    className="text-primary font-semibold hover:underline disabled:text-foreground/40"
                    onClick={() => void onResolve(attachment.object_id)}
                    disabled={isBusy}
                  >
                    Get link
                  </button>
                  {state?.error ? (
                    <span className="text-[11px] text-destructive">{state.error}</span>
                  ) : (
                    <span className="text-foreground/50">Link not ready</span>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
