import type { StoragePresignUploadResponse } from '@/lib/api/client/types.gen';

const mockObjects = [
  {
    id: 'obj-1',
    filename: 'transcript.pdf',
    object_key: 'uploads/transcript.pdf',
    mime_type: 'application/pdf',
    size_bytes: 128_000,
    conversation_id: 'conv-123',
  },
  {
    id: 'obj-2',
    filename: 'notes.txt',
    object_key: 'uploads/notes.txt',
    mime_type: 'text/plain',
    size_bytes: 4_200,
    conversation_id: null,
  },
];

export function useStorageObjectsInfiniteQuery() {
  return {
    data: {
      pages: [
        {
          items: mockObjects,
          next_offset: null,
        },
      ],
    },
    isLoading: false,
    isError: false,
    isFetching: false,
    isFetchingNextPage: false,
    hasNextPage: false,
    fetchNextPage: async () => {},
    refetch: async () => {},
  };
}

export function useDeleteStorageObject() {
  return {
    mutate: (id: string) => {
      console.log('delete storage object', id);
    },
    isPending: false,
  };
}

export function usePresignUpload() {
  return {
    mutateAsync: async () =>
      ({
        upload_url: 'https://example.com/upload',
        headers: {},
        method: 'PUT',
      } satisfies StoragePresignUploadResponse),
    isPending: false,
  };
}
