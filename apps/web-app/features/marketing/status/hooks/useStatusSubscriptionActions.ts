'use client';

import { useEffect, useMemo, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

import { unsubscribeStatusSubscription, verifyStatusSubscriptionToken } from '@/lib/api/statusSubscriptions';
import type { SubscriptionBanner } from '../utils/statusFormatting';

export function useStatusSubscriptionActions() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const verificationToken = searchParams.get('token');
  const verificationParam = searchParams.get('verification');
  const unsubscribeToken = searchParams.get('unsubscribe_token');
  const unsubscribeParam = searchParams.get('unsubscribe');
  const subscriptionIdentifier = searchParams.get('subscription_id');

  const verificationAttemptedRef = useRef(false);
  const unsubscribeAttemptedRef = useRef(false);

  useEffect(() => {
    if (!verificationToken || verificationAttemptedRef.current) {
      return;
    }

    verificationAttemptedRef.current = true;

    const redirectWithStatus = (state: 'success' | 'error') => {
      const params = new URLSearchParams(window.location.search);
      params.delete('token');
      params.delete('subscription_id');
      params.set('verification', state);
      const search = params.toString();
      router.replace(search ? `/status?${search}` : '/status', { scroll: false });
    };

    verifyStatusSubscriptionToken(verificationToken)
      .then(() => {
        redirectWithStatus('success');
      })
      .catch(() => {
        redirectWithStatus('error');
      });
  }, [verificationToken, router]);

  useEffect(() => {
    if (!unsubscribeToken || unsubscribeAttemptedRef.current) {
      return;
    }

    const redirectWithStatus = (state: 'success' | 'error') => {
      const params = new URLSearchParams(window.location.search);
      params.delete('unsubscribe_token');
      if (state === 'success' || !subscriptionIdentifier) {
        params.delete('subscription_id');
      }
      params.set('unsubscribe', state);
      const search = params.toString();
      router.replace(search ? `/status?${search}` : '/status', { scroll: false });
    };

    if (!subscriptionIdentifier) {
      unsubscribeAttemptedRef.current = true;
      redirectWithStatus('error');
      return;
    }

    unsubscribeAttemptedRef.current = true;

    unsubscribeStatusSubscription(unsubscribeToken, subscriptionIdentifier)
      .then(() => {
        redirectWithStatus('success');
      })
      .catch(() => {
        redirectWithStatus('error');
      });
  }, [unsubscribeToken, subscriptionIdentifier, router]);

  const banner: SubscriptionBanner | null = useMemo(() => {
    if (verificationToken && verificationParam === null) {
      return {
        tone: 'default',
        title: 'Confirming subscription…',
        description: 'Hang tight while we verify your email link.',
      };
    }

    if (unsubscribeToken && unsubscribeParam === null) {
      return {
        tone: 'default',
        title: 'Updating preferences…',
        description: 'Processing your unsubscribe request.',
      };
    }

    if (verificationParam === 'success') {
      return {
        tone: 'positive',
        title: 'Subscription confirmed',
        description: 'You will now receive email alerts whenever status changes.',
      };
    }

    if (verificationParam === 'error') {
      return {
        tone: 'warning',
        title: 'Unable to confirm subscription',
        description: 'The verification link may have expired. Request a new email to try again.',
      };
    }

    if (unsubscribeParam === 'success') {
      return {
        tone: 'positive',
        title: 'Subscription removed',
        description: 'You will no longer receive email updates from this list.',
      };
    }

    if (unsubscribeParam === 'error') {
      return {
        tone: 'warning',
        title: 'Unable to unsubscribe',
        description: 'The unsubscribe link may have expired. Request a fresh email to try again.',
      };
    }

    return null;
  }, [verificationParam, unsubscribeParam, verificationToken, unsubscribeToken]);

  const isProcessing = Boolean(
    (verificationToken && verificationParam === null) || (unsubscribeToken && unsubscribeParam === null),
  );

  return {
    banner,
    isProcessing,
  };
}
