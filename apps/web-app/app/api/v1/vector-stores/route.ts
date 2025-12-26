import { NextResponse } from 'next/server';

import { createVectorStoreApiV1VectorStoresPost, listVectorStoresApiV1VectorStoresGet } from '@/lib/api/client/sdk.gen';
import type { VectorStoreCreateRequest } from '@/lib/api/client/types.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

function resolveErrorMessage(error: unknown, fallback: string) {
  if (!error) return fallback;
  if (typeof error === 'string') return error;
  if (typeof error === 'object' && 'message' in error && typeof (error as { message?: unknown }).message === 'string') {
    return (error as { message: string }).message;
  }
  if (typeof error === 'object' && 'detail' in error) {
    const detail = (error as { detail?: unknown }).detail;
    if (typeof detail === 'string') return detail;
  }
  return fallback;
}

export async function GET() {
  try {
    const { client, auth } = await getServerApiClient();
    const res = await listVectorStoresApiV1VectorStoresGet({
      client,
      auth,
      throwOnError: false,
      responseStyle: 'fields',
    });
    if ('error' in res && res.error) {
      const status = res.response?.status ?? 500;
      const message = resolveErrorMessage(res.error, 'Failed to load vector stores');
      return NextResponse.json({ message }, { status });
    }
    return NextResponse.json(res.data ?? { items: [], total: 0 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load vector stores';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as VectorStoreCreateRequest;
    const { client, auth } = await getServerApiClient();
    const res = await createVectorStoreApiV1VectorStoresPost({
      client,
      auth,
      throwOnError: false,
      responseStyle: 'fields',
      body: payload,
    });
    if ('error' in res && res.error) {
      const status = res.response?.status ?? 500;
      const message = resolveErrorMessage(res.error, 'Failed to create vector store');
      return NextResponse.json({ message }, { status });
    }
    if (!res.data) return NextResponse.json({ message: 'Vector store create missing data' }, { status: 500 });
    return NextResponse.json(res.data);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to create vector store';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
