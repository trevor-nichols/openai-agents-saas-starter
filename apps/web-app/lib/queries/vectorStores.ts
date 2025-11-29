import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  attachVectorStoreFile,
  createVectorStore,
  deleteVectorStore,
  deleteVectorStoreFile,
  listVectorStoreFiles,
  listVectorStores,
  searchVectorStore,
} from '@/lib/api/vectorStores';
import type {
  VectorStoreCreateRequest,
  VectorStoreFileCreateRequest,
  VectorStoreSearchRequest,
} from '@/lib/api/client/types.gen';
import { queryKeys } from './keys';

export function useVectorStoresQuery() {
  return useQuery({ queryKey: queryKeys.vectorStores.list(), queryFn: listVectorStores });
}

export function useVectorStoreFilesQuery(vectorStoreId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.vectorStores.files(vectorStoreId),
    queryFn: () => listVectorStoreFiles(vectorStoreId),
    enabled,
  });
}

export function useCreateVectorStore() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: VectorStoreCreateRequest) => createVectorStore(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.vectorStores.list() }).catch(() => {});
    },
  });
}

export function useDeleteVectorStore() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteVectorStore(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.vectorStores.list() }).catch(() => {});
    },
  });
}

export function useAttachVectorStoreFile(vectorStoreId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: VectorStoreFileCreateRequest) => attachVectorStoreFile(vectorStoreId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.vectorStores.files(vectorStoreId) }).catch(() => {});
    },
  });
}

export function useDeleteVectorStoreFile(vectorStoreId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (fileId: string) => deleteVectorStoreFile(vectorStoreId, fileId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.vectorStores.files(vectorStoreId) }).catch(() => {});
    },
  });
}

export function useSearchVectorStore(vectorStoreId: string) {
  return useMutation({
    mutationFn: (body: VectorStoreSearchRequest) => searchVectorStore(vectorStoreId, body),
  });
}
