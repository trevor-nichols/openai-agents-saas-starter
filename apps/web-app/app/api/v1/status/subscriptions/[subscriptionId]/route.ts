import { NextRequest, NextResponse } from 'next/server';

import { revokeStatusSubscriptionApiV1StatusSubscriptionsSubscriptionIdDelete } from '@/lib/api/client/sdk.gen';
import { unsubscribeStatusSubscriptionViaToken } from '@/lib/server/services/statusSubscriptions';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function DELETE(request: NextRequest, { params }: { params: Promise<{ subscriptionId: string }> }) {
  const { subscriptionId } = await params;
  if (!subscriptionId) {
    return NextResponse.json({ message: 'subscriptionId is required' }, { status: 400 });
  }

  const token = request.nextUrl.searchParams.get('token');

  try {
    if (token) {
      await unsubscribeStatusSubscriptionViaToken({ subscriptionId, token });
      return NextResponse.json({ success: true }, { status: 200 });
    }

    const { client, auth } = await getServerApiClient();
    await revokeStatusSubscriptionApiV1StatusSubscriptionsSubscriptionIdDelete({
      client,
      auth,
      throwOnError: true,
      path: { subscription_id: subscriptionId },
    });
    return NextResponse.json({ success: true }, { status: 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unable to revoke subscription.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
