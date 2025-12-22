'use client';

import { useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { GlassPanel } from '@/components/ui/foundation';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import { useToast } from '@/components/ui/use-toast';
import {
  useCreateVectorStore,
  useDeleteVectorStore,
  useDeleteVectorStoreFile,
  useUploadVectorStoreFile,
  useVectorStoreFilesQuery,
  useVectorStoresQuery,
} from '@/lib/queries/vectorStores';
import { useFileSearchAgents } from '@/lib/queries/agents';
import { useConversationsByAgent } from '@/lib/queries/conversations';
import { usePresignUpload } from '@/lib/queries/storageObjects';
import { uploadFileToPresignedUrl } from '@/lib/storage/upload';

const UNASSIGNED_OPTION = 'unassigned';

export function VectorStoresPanel() {
  const vectorStoresQuery = useVectorStoresQuery();
  const createVector = useCreateVectorStore();
  const deleteVector = useDeleteVectorStore();
  const { error: showErrorToast, success: showSuccessToast } = useToast();
  const [selectedVs, setSelectedVs] = useState<string | null>(null);
  const filesQuery = useVectorStoreFilesQuery(selectedVs ?? 'vs-placeholder', Boolean(selectedVs));
  const deleteFile = useDeleteVectorStoreFile(selectedVs ?? '');
  const presignUpload = usePresignUpload();
  const uploadVectorStoreFile = useUploadVectorStoreFile();

  const [newVsName, setNewVsName] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [uploadInputKey, setUploadInputKey] = useState(0);
  const isUploading = presignUpload.isPending || uploadVectorStoreFile.isPending;
  const [selectedAgentKey, setSelectedAgentKey] = useState<string | null>(null);
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);

  const {
    agents: fileSearchAgents,
    isLoadingAgents,
    agentsError,
  } = useFileSearchAgents();
  const {
    conversations: agentConversations,
    isLoadingConversations,
    conversationsError,
  } = useConversationsByAgent(selectedAgentKey, { limit: 100 });

  const agentOptions = useMemo(
    () =>
      fileSearchAgents.map((agent) => ({
        value: agent.name,
        label: agent.display_name ?? agent.name,
        description: agent.description ?? null,
      })),
    [fileSearchAgents],
  );

  const conversationOptions = useMemo(
    () =>
      agentConversations.map((conversation) => ({
        value: conversation.id,
        label:
          conversation.display_name ??
          conversation.title ??
          conversation.last_message_preview ??
          `Conversation ${conversation.id.slice(0, 8)}`,
        description: conversation.last_message_preview ?? null,
      })),
    [agentConversations],
  );

  return (
    <GlassPanel className="p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold">Vector Stores</h3>
          <p className="text-xs text-foreground/60">Create stores and attach uploaded files.</p>
        </div>
        <Button size="sm" variant="outline" onClick={() => vectorStoresQuery.refetch()} disabled={vectorStoresQuery.isLoading}>
          Refresh
        </Button>
      </div>

      <div className="flex gap-2 items-end">
        <div className="space-y-1">
          <Label className="text-xs text-foreground/70">Name</Label>
          <Input value={newVsName} onChange={(e) => setNewVsName(e.target.value)} placeholder="New vector store" />
        </div>
        <Button
          size="sm"
          onClick={() => {
            const trimmed = newVsName.trim();
            if (!trimmed) return;
            createVector.mutate(
              { name: trimmed, description: null, metadata: null, expires_after: null },
              {
                onSuccess: () => setNewVsName(''),
                onError: (error) => {
                  const message = error instanceof Error ? error.message : 'Unable to create vector store.';
                  showErrorToast({ title: 'Vector store create failed', description: message });
                },
              },
            );
          }}
          disabled={createVector.isPending}
        >
          Create
        </Button>
      </div>

      {vectorStoresQuery.isLoading ? (
        <SkeletonPanel lines={6} />
      ) : vectorStoresQuery.isError ? (
        <ErrorState
          title="Failed to load vector stores"
          message={
            vectorStoresQuery.error instanceof Error ? vectorStoresQuery.error.message : undefined
          }
        />
      ) : (vectorStoresQuery.data?.items?.length ?? 0) === 0 ? (
        <EmptyState title="No vector stores" description="Create a store to attach files." />
      ) : (
        <div className="grid gap-2">
          {(vectorStoresQuery.data?.items ?? []).map((vs) => (
            <div
              key={vs.id}
              className="rounded-lg border border-white/5 bg-white/5 p-3 flex items-center justify-between gap-3"
            >
              <div>
                <div className="font-semibold">{vs.name}</div>
                <div className="text-xs text-foreground/60">{vs.description ?? '—'}</div>
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant={selectedVs === vs.id ? 'default' : 'secondary'} onClick={() => setSelectedVs(vs.id)}>
                  {selectedVs === vs.id ? 'Selected' : 'Files'}
                </Button>
                <Button size="sm" variant="ghost" onClick={() => deleteVector.mutate(vs.id)} disabled={deleteVector.isPending}>
                  Delete
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedVs ? (
        <div className="space-y-2 rounded-lg border border-white/5 bg-white/5 p-3">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold">Files</div>
            <Button size="sm" variant="outline" onClick={() => filesQuery.refetch()} disabled={filesQuery.isLoading}>
              Refresh
            </Button>
          </div>
          {filesQuery.isLoading ? (
            <SkeletonPanel lines={3} />
          ) : filesQuery.isError ? (
            <ErrorState title="Failed to load files" />
          ) : filesQuery.data?.items.length ? (
            <div className="space-y-2">
              {filesQuery.data.items.map((file) => (
                <div key={file.id} className="flex items-center justify-between rounded-md border border-white/5 px-3 py-2 text-sm">
                  <span>{file.filename}</span>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => selectedVs && deleteFile.mutate(file.id)}
                    disabled={deleteFile.isPending || !selectedVs}
                  >
                    Remove file
                  </Button>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="No files" description="Attach files to index them." />
          )}

          <div className="space-y-2">
            <Label className="text-xs text-foreground/70">Upload file to vector store</Label>
            <div className="grid gap-2 md:grid-cols-2">
              <div className="space-y-1">
                <Label className="text-[11px] uppercase tracking-wide text-foreground/60">
                  Agent (file_search)
                </Label>
                <Select
                  value={selectedAgentKey ?? UNASSIGNED_OPTION}
                  onValueChange={(value) => {
                    const next = value === UNASSIGNED_OPTION ? null : value;
                    setSelectedAgentKey(next);
                    setSelectedConversationId(null);
                  }}
                  disabled={isLoadingAgents || Boolean(agentsError)}
                >
                  <SelectTrigger>
                    <SelectValue
                      placeholder={
                        isLoadingAgents
                          ? 'Loading agents…'
                          : agentOptions.length
                            ? 'Select an agent'
                            : 'No file_search agents'
                      }
                    />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={UNASSIGNED_OPTION}>No agent gating</SelectItem>
                    {agentOptions.map((agent) => (
                      <SelectItem key={agent.value} value={agent.value}>
                        <div className="space-y-1">
                          <div className="font-medium">{agent.label}</div>
                          {agent.description ? (
                            <div className="text-xs text-muted-foreground">{agent.description}</div>
                          ) : null}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {agentsError ? (
                  <p className="text-xs text-destructive">Unable to load agents.</p>
                ) : null}
              </div>
              <div className="space-y-1">
                <Label className="text-[11px] uppercase tracking-wide text-foreground/60">
                  Conversation
                </Label>
                <Select
                  value={selectedConversationId ?? UNASSIGNED_OPTION}
                  onValueChange={(value) =>
                    setSelectedConversationId(value === UNASSIGNED_OPTION ? null : value)
                  }
                  disabled={!selectedAgentKey || isLoadingConversations || Boolean(conversationsError)}
                >
                  <SelectTrigger>
                    <SelectValue
                      placeholder={
                        !selectedAgentKey
                          ? 'Select an agent first'
                          : isLoadingConversations
                            ? 'Loading conversations…'
                            : conversationOptions.length
                              ? 'Select a conversation'
                              : 'No conversations found'
                      }
                    />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={UNASSIGNED_OPTION}>No conversation</SelectItem>
                    {conversationOptions.map((conversation) => (
                      <SelectItem key={conversation.value} value={conversation.value}>
                        <div className="space-y-1">
                          <div className="font-medium">{conversation.label}</div>
                          {conversation.description ? (
                            <div className="text-xs text-muted-foreground">
                              {conversation.description}
                            </div>
                          ) : null}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {conversationsError ? (
                  <p className="text-xs text-destructive">Unable to load conversations.</p>
                ) : null}
              </div>
            </div>
            <Input
              key={uploadInputKey}
              type="file"
              disabled={isUploading}
              onChange={(event) => {
                const file = event.target.files?.[0] ?? null;
                setUploadFile(file);
              }}
              className="max-w-xs"
            />
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                onClick={async () => {
                  if (!selectedVs) {
                    showErrorToast({
                      title: 'Select a vector store',
                      description: 'Choose a destination store.',
                    });
                    return;
                  }
                  if (!uploadFile) {
                    showErrorToast({ title: 'Choose a file first', description: 'Select a file to upload.' });
                    return;
                  }

                  try {
                    setUploadStatus('Requesting upload URL…');
                    const presign = await presignUpload.mutateAsync({
                      filename: uploadFile.name,
                      mime_type: uploadFile.type || 'application/octet-stream',
                      size_bytes: uploadFile.size,
                      conversation_id: selectedConversationId,
                      agent_key: selectedAgentKey,
                      metadata: {
                        source: 'storage_vector_store',
                      },
                    });

                    setUploadStatus('Uploading file…');
                    await uploadFileToPresignedUrl(presign, uploadFile);

                    setUploadStatus('Indexing in vector store…');
                    await uploadVectorStoreFile.mutateAsync({
                      vectorStoreId: selectedVs,
                      body: {
                        object_id: presign.object_id,
                        attributes: { filename: uploadFile.name },
                      },
                    });

                    setUploadStatus('Upload complete');
                    showSuccessToast({
                      title: 'File uploaded',
                      description: `${uploadFile.name} is now attached to the vector store.`,
                    });
                    setUploadFile(null);
                    setUploadInputKey((prev) => prev + 1);
                  } catch (error) {
                    const message = error instanceof Error ? error.message : 'Upload failed';
                    setUploadStatus(null);
                    showErrorToast({ title: 'Upload failed', description: message });
                  }
                }}
                disabled={isUploading || !uploadFile || !selectedVs}
              >
                {isUploading ? 'Uploading…' : 'Upload file'}
              </Button>
              {uploadStatus ? <span className="text-xs text-foreground/60">{uploadStatus}</span> : null}
            </div>
          </div>
        </div>
      ) : null}
    </GlassPanel>
  );
}
