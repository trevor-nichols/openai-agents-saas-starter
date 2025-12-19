import { useCallback, useState } from 'react';

import { useToast } from '@/components/ui/use-toast';
import { getAttachmentDownloadUrl } from '@/lib/api/storage';
import { createLogger } from '@/lib/logging';

export type AttachmentState = Record<string, { url?: string; error?: string; loading?: boolean }>;

const log = createLogger('attachments');

export function useAttachmentResolver() {
  const [attachmentState, setAttachmentState] = useState<AttachmentState>({});
  const { error: showErrorToast, success: showSuccessToast } = useToast();

  const resolveAttachment = useCallback(
    async (objectId: string) => {
      setAttachmentState((prev) => ({
        ...prev,
        [objectId]: { ...prev[objectId], loading: true, error: undefined },
      }));
      try {
        const presign = await getAttachmentDownloadUrl(objectId);
        setAttachmentState((prev) => ({
          ...prev,
          [objectId]: { ...prev[objectId], url: presign.download_url, loading: false },
        }));
        log.debug('Resolved attachment download', { objectId });
        showSuccessToast({ title: 'Attachment link ready' });
      } catch (error) {
        setAttachmentState((prev) => ({
          ...prev,
          [objectId]: {
            ...prev[objectId],
            loading: false,
            error: error instanceof Error ? error.message : 'Unable to fetch link',
          },
        }));
        log.debug('Attachment download failed', { objectId, error });
        showErrorToast({
          title: 'Attachment link unavailable',
          description:
            error instanceof Error ? error.message : 'Could not fetch a download link. Please try again.',
        });
      }
    },
    [showErrorToast, showSuccessToast],
  );

  return { attachmentState, resolveAttachment } as const;
}

