export async function getAttachmentDownloadUrl(objectId: string) {
  console.log('mock download url for', objectId);
  return { download_url: 'https://example.com/download/mock-file' };
}
