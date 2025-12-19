const mockVectorStores = [
  { id: 'vs-1', name: 'Product KB', description: 'Customer-facing docs' },
  { id: 'vs-2', name: 'Engineering Notes', description: 'Design docs and ADRs' },
];

const mockFiles = [
  { id: 'file-1', filename: 'kb-intro.pdf' },
  { id: 'file-2', filename: 'adr-001.md' },
];

export function useVectorStoresQuery() {
  return {
    data: { items: mockVectorStores },
    isLoading: false,
    isError: false,
    refetch: async () => {},
  };
}

export function useCreateVectorStore() {
  return {
    mutate: (body: unknown) => {
      console.log('create vector store', body);
    },
    isPending: false,
  };
}

export function useDeleteVectorStore() {
  return {
    mutate: (id: string) => {
      console.log('delete vector store', id);
    },
    isPending: false,
  };
}

export function useVectorStoreFilesQuery() {
  return {
    data: { items: mockFiles },
    isLoading: false,
    isError: false,
    refetch: async () => {},
  };
}

export function useAttachVectorStoreFile() {
  return {
    mutate: (body: unknown) => {
      console.log('attach vector store file', body);
    },
    isPending: false,
  };
}

export function useDeleteVectorStoreFile() {
  return {
    mutate: (id: string) => {
      console.log('delete vector store file', id);
    },
    isPending: false,
  };
}

export function useSearchVectorStore() {
  return {
    mutateAsync: async (body: unknown) => {
      console.log('search vector store', body);
      return { results: [] };
    },
  };
}

export function useBindAgentToVectorStore() {
  return {
    mutate: (agentKey: string) => {
      console.log('bind agent', agentKey);
    },
  };
}

export function useUnbindAgentFromVectorStore() {
  return {
    mutate: (agentKey: string) => {
      console.log('unbind agent', agentKey);
    },
  };
}
