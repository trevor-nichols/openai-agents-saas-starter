'use client';

import { UploadCloud, X } from 'lucide-react';
import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';
import { cn } from '@/lib/utils';
import { usePresignUpload } from '@/lib/queries/storageObjects';
import { uploadFileToPresignedUrl } from '@/lib/storage/upload';

interface UploadObjectFormProps {
  onUploaded?: () => void;
}

export function UploadObjectForm({ onUploaded }: UploadObjectFormProps) {
  const [conversationId, setConversationId] = useState('');
  const [agentKey, setAgentKey] = useState('');
  const [status, setStatus] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const presignUpload = usePresignUpload();
  const { error: showErrorToast, success: showSuccessToast } = useToast();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      setSelectedFile(file);
      setStatus(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    disabled: isUploading,
  });

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setStatus('Requesting upload URL…');

    try {
      const presign = await presignUpload.mutateAsync({
        filename: selectedFile.name,
        mime_type: selectedFile.type || 'application/octet-stream',
        size_bytes: selectedFile.size,
        conversation_id: conversationId.trim() || null,
        agent_key: agentKey.trim() || null,
        metadata: null,
      });

      setStatus('Uploading…');
      await uploadFileToPresignedUrl(presign, selectedFile);

      showSuccessToast({ title: 'Upload complete', description: `${selectedFile.name} uploaded.` });
      setSelectedFile(null);
      setConversationId('');
      setStatus(null);
      onUploaded?.();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Upload failed';
      setStatus('Failed');
      showErrorToast({ title: 'Upload failed', description: message });
    } finally {
      setIsUploading(false);
    }
  };

  const clearFile = (e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedFile(null);
    setStatus(null);
  };

  return (
    <div className="space-y-4 rounded-lg border border-border/50 bg-background/50 p-4">
      <div
        {...getRootProps()}
        className={cn(
          'relative flex flex-col items-center justify-center rounded-md border-2 border-dashed border-muted-foreground/25 bg-muted/5 px-6 py-10 transition-colors hover:bg-muted/10',
          isDragActive && 'border-primary/50 bg-primary/5',
          isUploading && 'opacity-50 cursor-not-allowed'
        )}
      >
        <input {...getInputProps()} />
        
        {selectedFile ? (
          <div className="flex flex-col items-center gap-2 text-center">
            <div className="rounded-full bg-primary/10 p-3 text-primary">
              <UploadCloud className="h-6 w-6" />
            </div>
            <div className="text-sm font-medium">{selectedFile.name}</div>
            <div className="text-xs text-muted-foreground">
              {(selectedFile.size / 1024).toFixed(1)} KB • {selectedFile.type || 'Unknown type'}
            </div>
            {!isUploading && (
              <Button
                size="sm"
                variant="ghost"
                className="mt-2 h-auto py-1 text-xs text-destructive hover:text-destructive"
                onClick={clearFile}
              >
                <X className="mr-1 h-3 w-3" /> Remove
              </Button>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 text-center">
            <UploadCloud className="h-8 w-8 text-muted-foreground/50" />
            <div className="text-sm font-medium text-foreground">
              {isDragActive ? 'Drop file here' : 'Drag & drop or click to upload'}
            </div>
            <p className="text-xs text-muted-foreground">
              Max 256 filename chars. Size & mime type validated on presign.
            </p>
          </div>
        )}
      </div>

      {selectedFile && (
        <div className="grid gap-4 md:grid-cols-[1fr_1fr_auto] items-end animate-in fade-in slide-in-from-top-2">
          <div className="space-y-1.5">
            <Label className="text-xs font-medium text-muted-foreground">Conversation ID (Optional)</Label>
            <Input
              value={conversationId}
              onChange={(e) => setConversationId(e.target.value)}
              placeholder="UUID"
              className="h-8 text-sm bg-background/50"
              disabled={isUploading}
            />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs font-medium text-muted-foreground">Agent Key (Optional)</Label>
            <Input
              value={agentKey}
              onChange={(e) => setAgentKey(e.target.value)}
              placeholder="agent-key"
              className="h-8 text-sm bg-background/50"
              disabled={isUploading}
            />
          </div>
          <Button 
            size="sm" 
            onClick={handleUpload} 
            disabled={isUploading || presignUpload.isPending}
            className="h-8"
          >
            {isUploading ? (
              <>
                <span className="mr-2 animate-spin">⟳</span>
                {status || 'Uploading'}
              </>
            ) : (
              'Upload File'
            )}
          </Button>
        </div>
      )}
    </div>
  );
}
