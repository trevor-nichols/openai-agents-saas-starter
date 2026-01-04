'use server';

import { getApiBaseUrl, getServerApiClient } from '../apiClient';

export interface OpenAiDownloadResult {
  ok: boolean;
  status: number;
  stream: ReadableStream<Uint8Array> | null;
  headers: Headers;
}

function buildDownloadHeaders(response: Response): Headers {
  const headers = new Headers();
  const contentType = response.headers.get('content-type');
  const disposition = response.headers.get('content-disposition');
  const cacheControl = response.headers.get('cache-control');
  if (contentType) headers.set('content-type', contentType);
  if (disposition) headers.set('content-disposition', disposition);
  if (cacheControl) headers.set('cache-control', cacheControl);
  return headers;
}

async function proxyDownload(
  url: string,
  options?: { signal?: AbortSignal },
): Promise<OpenAiDownloadResult> {
  const { auth } = await getServerApiClient();
  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${auth()}`,
    },
    cache: 'no-store',
    signal: options?.signal,
  });

  return {
    ok: response.ok,
    status: response.status,
    stream: response.body,
    headers: buildDownloadHeaders(response),
  };
}

export async function downloadOpenAiFile(params: {
  fileId: string;
  search?: string;
  signal?: AbortSignal;
}): Promise<OpenAiDownloadResult> {
  if (!params.fileId) {
    throw new Error('fileId is required.');
  }

  const baseUrl = getApiBaseUrl();
  const search = params.search ?? '';
  const url = `${baseUrl}/api/v1/openai/files/${params.fileId}/download${search}`;
  return proxyDownload(url, { signal: params.signal });
}

export async function downloadOpenAiContainerFile(params: {
  containerId: string;
  fileId: string;
  search?: string;
  signal?: AbortSignal;
}): Promise<OpenAiDownloadResult> {
  if (!params.containerId || !params.fileId) {
    throw new Error('containerId and fileId are required.');
  }

  const baseUrl = getApiBaseUrl();
  const search = params.search ?? '';
  const url = `${baseUrl}/api/v1/openai/containers/${params.containerId}/files/${params.fileId}/download${search}`;
  return proxyDownload(url, { signal: params.signal });
}
