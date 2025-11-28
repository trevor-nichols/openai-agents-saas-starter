import type {
  StorageObjectListResponse,
  StorageObjectResponse,
  StoragePresignUploadResponse,
  StoragePresignUploadRequest,
} from '@/lib/api/client/types.gen';

export type StorageObject = StorageObjectResponse;
export type StorageObjectList = StorageObjectListResponse;
export type StoragePresignUploadReq = StoragePresignUploadRequest;
export type StoragePresignUploadRes = StoragePresignUploadResponse;
