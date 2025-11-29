import type { StorageObject, StoragePresignUploadRes } from './types';

export const mockStorageObjects: StorageObject[] = [
  {
    id: 'obj-1',
    bucket: 'mock-bucket',
    object_key: 'uploads/doc.pdf',
    filename: 'doc.pdf',
    mime_type: 'application/pdf',
    size_bytes: 2048,
    status: 'stored',
    created_at: new Date().toISOString(),
    conversation_id: 'conv-1',
    agent_key: 'triage',
  },
];

export const mockPresignUpload: StoragePresignUploadRes = {
  object_id: 'obj-new',
  upload_url: 'https://example.com/upload',
  method: 'PUT',
  headers: {},
  bucket: 'mock-bucket',
  object_key: 'uploads/mock',
  expires_in_seconds: 300,
};
