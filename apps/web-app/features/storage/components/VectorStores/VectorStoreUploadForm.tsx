'use client';

import { useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useFileSearchAgents } from '@/lib/queries/agents';
import { useConversationsByAgent } from '@/lib/queries/conversations';

import { useVectorStoreUpload } from '../../hooks/useVectorStoreUpload';
import { buildAgentOptions, buildConversationOptions } from '../../utils/vectorStoreOptions';
import { AgentSelector } from './AgentSelector';
import { ConversationSelector } from './ConversationSelector';

interface VectorStoreUploadFormProps {
  vectorStoreId: string;
}

export function VectorStoreUploadForm({ vectorStoreId }: VectorStoreUploadFormProps) {
  const [selectedAgentKey, setSelectedAgentKey] = useState<string | null>(null);
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadInputKey, setUploadInputKey] = useState(0);

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
    () => buildAgentOptions(fileSearchAgents),
    [fileSearchAgents],
  );

  const conversationOptions = useMemo(
    () => buildConversationOptions(agentConversations),
    [agentConversations],
  );

  const { upload, isUploading, uploadStatus, resetStatus } = useVectorStoreUpload({
    vectorStoreId,
    agentKey: selectedAgentKey,
    conversationId: selectedConversationId,
  });

  const handleUpload = async () => {
    const success = await upload(uploadFile);
    if (success) {
      setUploadFile(null);
      setUploadInputKey((prev) => prev + 1);
    }
  };

  return (
    <div className="space-y-2">
      <Label className="text-xs text-foreground/70">Upload file to vector store</Label>
      <div className="grid gap-2 md:grid-cols-2">
        <AgentSelector
          value={selectedAgentKey}
          options={agentOptions}
          isLoading={isLoadingAgents}
          error={agentsError}
          onChange={(next) => {
            setSelectedAgentKey(next);
            setSelectedConversationId(null);
            resetStatus();
          }}
        />
        <ConversationSelector
          value={selectedConversationId}
          options={conversationOptions}
          isLoading={isLoadingConversations}
          error={conversationsError}
          hasAgent={Boolean(selectedAgentKey)}
          onChange={(next) => {
            setSelectedConversationId(next);
            resetStatus();
          }}
        />
      </div>
      <Input
        key={uploadInputKey}
        type="file"
        disabled={isUploading}
        onChange={(event) => {
          const file = event.target.files?.[0] ?? null;
          setUploadFile(file);
          resetStatus();
        }}
        className="max-w-xs"
      />
      <div className="flex items-center gap-2">
        <Button size="sm" onClick={handleUpload} disabled={isUploading || !uploadFile}>
          {isUploading ? 'Uploading…' : 'Upload file'}
        </Button>
        {uploadStatus ? <span className="text-xs text-foreground/60">{uploadStatus}</span> : null}
      </div>
    </div>
  );
}
