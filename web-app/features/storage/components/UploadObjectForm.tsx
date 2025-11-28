'use client';

import { useRef, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';
import { usePresignUpload } from '@/lib/queries/storageObjects';
import { uploadFileToPresignedUrl } from '@/lib/storage/upload';

interface UploadObjectFormProps {
  onUploaded?: () => void;
}

export function UploadObjectForm({ onUploaded }: UploadObjectFormProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [conversationId, setConversationId] = useState('');
  const [agentKey, setAgentKey] = useState('');
  const [status, setStatus] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const presignUpload = usePresignUpload();
  const { error: showErrorToast, success: showSuccessToast } = useToast();

  const handleUpload = async () => {
    const file = fileInputRef.current?.files?.[0];
    if (!file) {
      showErrorToast({ title: 'Choose a file first', description: 'Select a file to upload.' });
      return;
    }

    setIsUploading(true);
    setStatus('Requesting upload URL…');

    try {
      const presign = await presignUpload.mutateAsync({
        filename: file.name,
        mime_type: file.type || 'application/octet-stream',
        size_bytes: file.size,
        conversation_id: conversationId.trim() || null,
        agent_key: agentKey.trim() || null,
        metadata: null,
      });

      setStatus('Uploading…');
      await uploadFileToPresignedUrl(presign, file);

      setStatus('Uploaded');
      showSuccessToast({ title: 'Upload complete', description: `${file.name} uploaded.` });
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      onUploaded?.();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Upload failed';
      setStatus(message);
      showErrorToast({ title: 'Upload failed', description: message });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-3">
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        <div className="space-y-1">
          <Label className="text-xs text-foreground/70">File</Label>
          <Input ref={fileInputRef} type="file" disabled={isUploading} />
        </div>
        <div className="space-y-1">
          <Label className="text-xs text-foreground/70">Conversation ID (optional)</Label>
          <Input
            value={conversationId}
            onChange={(e) => setConversationId(e.target.value)}
            placeholder="uuid"
            disabled={isUploading}
          />
        </div>
        <div className="space-y-1">
          <Label className="text-xs text-foreground/70">Agent key (optional)</Label>
          <Input
            value={agentKey}
            onChange={(e) => setAgentKey(e.target.value)}
            placeholder="agent-key"
            disabled={isUploading}
          />
        </div>
      </div>
      <div className="flex items-center gap-3">
        <Button size="sm" onClick={handleUpload} disabled={isUploading || presignUpload.isPending}>
          {isUploading || presignUpload.isPending ? 'Working…' : 'Upload file'}
        </Button>
        <span className="text-xs text-foreground/60">{status ?? 'Max 256 filename chars; validates size & mime type via presign.'}</span>
      </div>
    </div>
  );
}
