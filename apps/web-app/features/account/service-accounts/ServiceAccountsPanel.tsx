'use client';

import { useCallback, useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { GlassPanel, SectionHeader } from '@/components/ui/foundation';
import { ErrorState } from '@/components/ui/states';
import { useToast } from '@/components/ui/use-toast';
import { useAccountProfileQuery } from '@/lib/queries/account';
import {
  useIssueServiceAccountTokenMutation,
  useRevokeServiceAccountTokenMutation,
  useServiceAccountTokensQuery,
} from '@/lib/queries/accountServiceAccounts';
import type {
  ServiceAccountIssueResult,
  ServiceAccountStatusFilter,
  ServiceAccountTokenRow,
} from '@/types/serviceAccounts';

import { SERVICE_ACCOUNT_DEFAULT_LIMIT } from './constants';
import { ServiceAccountFilters } from './components/ServiceAccountFilters';
import { ServiceAccountGuidance } from './components/ServiceAccountGuidance';
import { ServiceAccountStats } from './components/ServiceAccountStats';
import { ServiceAccountTable } from './components/ServiceAccountTable';
import { IssueTokenDialog } from './components/IssueTokenDialog';
import { RevokeTokenDialog } from './components/RevokeTokenDialog';
import { useDebouncedValue } from './hooks/useDebouncedValue';
import {
  buildIssuePayload,
  createDefaultIssueForm,
  type ServiceAccountIssueFormValues,
} from './utils/issueForm';

export function ServiceAccountsPanel() {
  const toast = useToast();
  const { profile } = useAccountProfileQuery();
  const defaultTenantId = profile?.tenant?.id ?? null;

  const [accountSearch, setAccountSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<ServiceAccountStatusFilter>('active');
  const debouncedAccount = useDebouncedValue(accountSearch, 350);

  const queryFilters = useMemo(
    () => ({
      account: debouncedAccount || undefined,
      status: statusFilter,
      limit: SERVICE_ACCOUNT_DEFAULT_LIMIT,
      offset: 0,
    }),
    [debouncedAccount, statusFilter],
  );

  const tokensQuery = useServiceAccountTokensQuery(queryFilters);
  const revokeMutation = useRevokeServiceAccountTokenMutation();
  const issueMutation = useIssueServiceAccountTokenMutation();

  const [selectedToken, setSelectedToken] = useState<ServiceAccountTokenRow | null>(null);
  const [revokeReason, setRevokeReason] = useState('');

  const [issueDialogOpen, setIssueDialogOpen] = useState(false);
  const [issueForm, setIssueForm] = useState<ServiceAccountIssueFormValues>(() => createDefaultIssueForm(defaultTenantId));
  const [issuedToken, setIssuedToken] = useState<ServiceAccountIssueResult | null>(null);
  const [issueFormError, setIssueFormError] = useState<string | null>(null);

  const openRevokeDialog = useCallback((token: ServiceAccountTokenRow) => {
    setSelectedToken(token);
    setRevokeReason('');
  }, []);

  const closeRevokeDialog = useCallback(() => {
    setSelectedToken(null);
    setRevokeReason('');
  }, []);

  const handleConfirmRevoke = useCallback(async () => {
    if (!selectedToken) return;
    try {
      await revokeMutation.mutateAsync({ tokenId: selectedToken.id, reason: revokeReason });
      toast.success({ title: 'Token revoked', description: `${selectedToken.account} tokens can no longer refresh.` });
      closeRevokeDialog();
    } catch (error) {
      toast.error({
        title: 'Unable to revoke token',
        description: error instanceof Error ? error.message : 'Try again shortly.',
      });
    }
  }, [closeRevokeDialog, revokeMutation, revokeReason, selectedToken, toast]);

  const handleIssueSubmit = useCallback(async () => {
    setIssueFormError(null);
    let payload;
    try {
      payload = buildIssuePayload(issueForm, defaultTenantId);
    } catch (error) {
      setIssueFormError(error instanceof Error ? error.message : 'Check the form and try again.');
      return;
    }

    try {
      const result = await issueMutation.mutateAsync(payload);
      setIssuedToken(result);
      toast.success({
        title: 'Token issued',
        description: 'Copy the refresh token now. It will not be shown again.',
      });
    } catch (error) {
      toast.error({
        title: 'Unable to issue token',
        description: error instanceof Error ? error.message : 'Try again shortly.',
      });
    }
  }, [defaultTenantId, issueForm, issueMutation, toast]);

  const tokens = tokensQuery.data?.tokens ?? [];
  const total = tokensQuery.data?.total ?? tokens.length;
  const isLoading = tokensQuery.isLoading;
  const loadError = tokensQuery.error instanceof Error ? tokensQuery.error.message : undefined;

  return (
    <section className="space-y-6">
      <SectionHeader
        eyebrow="Automation"
        title="Service-account tokens"
        description="Inspect automation credentials, audit scopes, and revoke stale tokens."
        actions={
          <Button
            size="sm"
            onClick={() => {
              setIssueForm(createDefaultIssueForm(defaultTenantId));
              setIssuedToken(null);
              setIssueFormError(null);
              setIssueDialogOpen(true);
            }}
          >
            Issue token
          </Button>
        }
      />

      <ServiceAccountStats
        total={total}
        onRefresh={() => tokensQuery.refetch()}
        isRefreshing={tokensQuery.isFetching}
      />

      <GlassPanel className="space-y-4">
        <ServiceAccountFilters
          accountSearch={accountSearch}
          status={statusFilter}
          onAccountSearchChange={setAccountSearch}
          onStatusChange={setStatusFilter}
        />

        {loadError && !isLoading ? (
          <ErrorState title="Unable to load tokens" message={loadError} onRetry={() => tokensQuery.refetch()} />
        ) : (
          <ServiceAccountTable
            tokens={tokens}
            isLoading={isLoading}
            onRevoke={openRevokeDialog}
            disableRevoke={revokeMutation.isPending}
          />
        )}
      </GlassPanel>

      <ServiceAccountGuidance />

      <RevokeTokenDialog
        token={selectedToken}
        reason={revokeReason}
        onReasonChange={setRevokeReason}
        onConfirm={handleConfirmRevoke}
        onClose={closeRevokeDialog}
        isSubmitting={revokeMutation.isPending}
      />

      <IssueTokenDialog
        open={issueDialogOpen}
        form={issueForm}
        onFormChange={setIssueForm}
        issuedToken={issuedToken}
        isSubmitting={issueMutation.isPending}
        formError={issueFormError}
        onSubmit={handleIssueSubmit}
        onDismiss={() => {
          setIssueDialogOpen(false);
          setIssueForm(createDefaultIssueForm(defaultTenantId));
          setIssueFormError(null);
          setIssuedToken(null);
        }}
        onIssueAnother={() => {
          setIssuedToken(null);
          setIssueForm(createDefaultIssueForm(defaultTenantId));
          setIssueFormError(null);
        }}
      />
    </section>
  );
}
