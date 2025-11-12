'use client';

import Link from 'next/link';
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ComponentProps,
  type Dispatch,
  type FormEvent,
  type SetStateAction,
} from 'react';
import type { ColumnDef } from '@tanstack/react-table';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { DataTable } from '@/components/ui/data-table';
import { GlassPanel, InlineTag, SectionHeader } from '@/components/ui/foundation';
import { Input } from '@/components/ui/input';
import { EmptyState, ErrorState } from '@/components/ui/states';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { useToast } from '@/components/ui/use-toast';
import { useAccountProfileQuery } from '@/lib/queries/account';
import {
  useIssueServiceAccountTokenMutation,
  useRevokeServiceAccountTokenMutation,
  useServiceAccountTokensQuery,
} from '@/lib/queries/accountServiceAccounts';
import type { ServiceAccountIssueResult, ServiceAccountStatusFilter, ServiceAccountTokenRow } from '@/types/serviceAccounts';
import {
  buildIssuePayload,
  createDefaultIssueForm,
  type ServiceAccountIssueFormValues,
} from './serviceAccountIssueHelpers';

const DEFAULT_LIMIT = 50;
const STATUS_OPTIONS: { label: string; value: ServiceAccountStatusFilter }[] = [
  { label: 'Active', value: 'active' },
  { label: 'Revoked', value: 'revoked' },
  { label: 'All', value: 'all' },
];

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
      limit: DEFAULT_LIMIT,
      offset: 0,
    }),
    [debouncedAccount, statusFilter],
  );

  const tokensQuery = useServiceAccountTokensQuery(queryFilters);
  const revokeMutation = useRevokeServiceAccountTokenMutation();
  const issueMutation = useIssueServiceAccountTokenMutation();

  const [dialogState, setDialogState] = useState<{
    token: ServiceAccountTokenRow | null;
    reason: string;
  }>({ token: null, reason: '' });

  const [issueDialogOpen, setIssueDialogOpen] = useState(false);
  const [issueForm, setIssueForm] = useState<ServiceAccountIssueFormValues>(() => createDefaultIssueForm(defaultTenantId));
  const [issuedToken, setIssuedToken] = useState<ServiceAccountIssueResult | null>(null);
  const [issueFormError, setIssueFormError] = useState<string | null>(null);

  useEffect(() => {
    if (!issueDialogOpen && defaultTenantId && !issueForm.tenantId) {
      setIssueForm((current) => ({ ...current, tenantId: defaultTenantId }));
    }
  }, [defaultTenantId, issueDialogOpen, issueForm.tenantId]);

  const openRevokeDialog = useCallback((token: ServiceAccountTokenRow) => {
    setDialogState({ token, reason: '' });
  }, []);

  const closeDialog = useCallback(() => {
    setDialogState({ token: null, reason: '' });
  }, []);

  const handleConfirmRevoke = useCallback(async () => {
    if (!dialogState.token) return;
    try {
      await revokeMutation.mutateAsync({
        tokenId: dialogState.token.id,
        reason: dialogState.reason,
      });
      toast.success({
        title: 'Token revoked',
        description: `${dialogState.token.account} tokens can no longer refresh.`,
      });
      closeDialog();
    } catch (error) {
      toast.error({
        title: 'Unable to revoke token',
        description: error instanceof Error ? error.message : 'Try again shortly.',
      });
    }
  }, [closeDialog, dialogState.reason, dialogState.token, revokeMutation, toast]);

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

  const columns = useMemo<ColumnDef<ServiceAccountTokenRow>[]>(
    () => [
      {
        header: 'Account',
        cell: ({ row }) => (
          <div className="flex flex-col">
            <span className="font-medium text-foreground">{row.original.account}</span>
            <span className="text-xs text-foreground/60">
              {row.original.fingerprint || row.original.id}
            </span>
          </div>
        ),
      },
      {
        header: 'Scopes',
        cell: ({ row }) => (
          <div className="flex flex-wrap gap-1">
            {row.original.scopes.map((scope) => (
              <InlineTag key={scope} tone="default">
                {scope}
              </InlineTag>
            ))}
          </div>
        ),
      },
      {
        header: 'Lifecycle',
        cell: ({ row }) => (
          <div className="flex flex-col text-sm">
            <span>Issued {formatDate(row.original.issuedAt)}</span>
            <span className="text-xs text-foreground/60">Expires {formatDate(row.original.expiresAt)}</span>
          </div>
        ),
      },
      {
        header: 'Status',
        cell: ({ row }) => {
          const status = resolveStatus(row.original);
          return <InlineTag tone={status.tone}>{status.label}</InlineTag>;
        },
      },
      {
        id: 'actions',
        header: 'Actions',
        cell: ({ row }) => (
          <Button
            size="sm"
            variant="outline"
            disabled={row.original.revokedAt !== null || revokeMutation.isPending}
            onClick={() => openRevokeDialog(row.original)}
          >
            Revoke
          </Button>
        ),
      },
    ],
    [openRevokeDialog, revokeMutation.isPending],
  );

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

      <GlassPanel className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm text-foreground/70">Total tokens</p>
            <p className="text-2xl font-semibold text-foreground">{total}</p>
          </div>
          <Button variant="outline" size="sm" onClick={() => tokensQuery.refetch()} disabled={tokensQuery.isFetching}>
            Refresh
          </Button>
        </div>
        <p className="text-sm text-foreground/60">
          Issue tokens directly from this dashboard (browser mode) or provide Vault headers for the compliance-approved
          issuance flow. Use the table below to audit and revoke credentials at any time.
        </p>
      </GlassPanel>

      <GlassPanel className="space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <Input
            className="w-full max-w-xs"
            placeholder="Search account"
            value={accountSearch}
            onChange={(event) => setAccountSearch(event.target.value)}
          />
          <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value as ServiceAccountStatusFilter)}>
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              {STATUS_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {loadError && !isLoading ? (
          <ErrorState
            title="Unable to load tokens"
            message={loadError}
            onRetry={() => tokensQuery.refetch()}
          />
        ) : (
          <DataTable<ServiceAccountTokenRow>
            columns={columns}
            data={tokens}
            isLoading={isLoading}
            emptyState={<EmptyState title="No service-account tokens" description="Issue a token via the Starter CLI to see it here." />}
          />
        )}
      </GlassPanel>

      <Alert>
        <AlertTitle>Need to run this in CI?</AlertTitle>
        <AlertDescription className="space-y-2 text-sm text-foreground/70">
          <p>
            Browser mode signs requests with your admin session. Switch to the Vault-signed mode if your organization
            requires pre-signed headers from Vault Transit. CI pipelines can continue using the CLI via
            <code className="ml-1 rounded bg-muted px-2 py-1 text-xs font-mono">starter_cli auth tokens issue-service-account</code>.
          </p>
          <p>
            Latest rollout status lives in
            <Link className="ml-1 underline" href="/docs/frontend/features/account-service-accounts.md">
              docs/frontend/features/account-service-accounts.md
            </Link>
            .
          </p>
        </AlertDescription>
      </Alert>

      <AlertDialog open={Boolean(dialogState.token)} onOpenChange={(open) => { if (!open) closeDialog(); }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Revoke {dialogState.token?.account}</AlertDialogTitle>
            <AlertDialogDescription>
              This immediately invalidates the refresh token. Automation pipelines using it will need a new credential.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="space-y-2 py-2">
            <Textarea
              placeholder="Optional reason (shown in audit logs)"
              value={dialogState.reason}
              onChange={(event) => setDialogState((current) => ({ ...current, reason: event.target.value }))}
              disabled={revokeMutation.isPending}
            />
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={revokeMutation.isPending}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={revokeMutation.isPending}
              onClick={handleConfirmRevoke}
            >
              Revoke token
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
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

type InlineTagTone = ComponentProps<typeof InlineTag>['tone'];

function resolveStatus(token: ServiceAccountTokenRow): { label: string; tone: InlineTagTone } {
  if (token.revokedAt) {
    return { label: 'Revoked', tone: 'warning' };
  }
  if (isPast(token.expiresAt)) {
    return { label: 'Expired', tone: 'default' };
  }
  return { label: 'Active', tone: 'positive' };
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '—';
  }
  return date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

function isPast(value: string): boolean {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return false;
  }
  return date.getTime() < Date.now();
}

function useDebouncedValue<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}

interface IssueTokenDialogProps {
  open: boolean;
  form: ServiceAccountIssueFormValues;
  onFormChange: Dispatch<SetStateAction<ServiceAccountIssueFormValues>>;
  issuedToken: ServiceAccountIssueResult | null;
  isSubmitting: boolean;
  formError: string | null;
  onSubmit: () => void | Promise<void>;
  onDismiss: () => void;
  onIssueAnother: () => void;
}

function IssueTokenDialog({
  open,
  form,
  onFormChange,
  issuedToken,
  isSubmitting,
  formError,
  onSubmit,
  onDismiss,
  onIssueAnother,
}: IssueTokenDialogProps) {
  const handleOpenChange = (next: boolean) => {
    if (!next) {
      onDismiss();
    }
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onSubmit();
  };

  const updateField = <K extends keyof ServiceAccountIssueFormValues>(field: K, value: ServiceAccountIssueFormValues[K]) => {
    onFormChange((current) => ({ ...current, [field]: value }));
  };

  const renderForm = () => (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <DialogHeader>
        <DialogTitle>Issue a new service-account token</DialogTitle>
        <DialogDescription>Fill in the account details and describe why you need this credential. The token is shown once.</DialogDescription>
      </DialogHeader>
      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="issue-mode">Issuance method</Label>
          <Select value={form.mode} onValueChange={(value) => updateField('mode', value as ServiceAccountIssueFormValues['mode'])}>
            <SelectTrigger id="issue-mode">
              <SelectValue placeholder="Select issuance mode" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="browser">Browser (signed via session)</SelectItem>
              <SelectItem value="vault">Vault-signed (headers supplied)</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-xs text-foreground/60">
            Browser mode signs on your behalf. Vault mode forwards the Vault Authorization + payload headers that you
            capture from Vault Transit or the Starter CLI.
          </p>
        </div>
        <div className="space-y-2">
          <Label htmlFor="issue-account">Account</Label>
          <Input
            id="issue-account"
            placeholder="analytics-batch"
            value={form.account}
            onChange={(event) => updateField('account', event.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="issue-scopes">Scopes</Label>
          <Textarea
            id="issue-scopes"
            placeholder="conversations:read, billing:use"
            value={form.scopes}
            onChange={(event) => updateField('scopes', event.target.value)}
          />
          <p className="text-xs text-foreground/60">Separate scopes with commas or newlines.</p>
        </div>
        <div className="space-y-2">
          <Label htmlFor="issue-tenant">Tenant ID</Label>
          <Input
            id="issue-tenant"
            placeholder="Tenant UUID"
            value={form.tenantId ?? ''}
            onChange={(event) => updateField('tenantId', event.target.value || null)}
          />
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="issue-lifetime">Lifetime (minutes)</Label>
            <Input
              id="issue-lifetime"
              type="number"
              min={1}
              placeholder="1440"
              value={form.lifetimeMinutes ?? ''}
              onChange={(event) =>
                updateField('lifetimeMinutes', event.target.value ? Number(event.target.value) : undefined)
              }
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="issue-fingerprint">Fingerprint (optional)</Label>
            <Input
              id="issue-fingerprint"
              placeholder="ci-runner-01"
              value={form.fingerprint ?? ''}
              onChange={(event) => updateField('fingerprint', event.target.value)}
            />
          </div>
        </div>
        <div className="flex items-center gap-3 rounded-lg border border-white/10 p-3">
          <div className="flex-1">
            <Label htmlFor="issue-force" className="text-sm font-medium">
              Force issuance
            </Label>
            <p className="text-xs text-foreground/60">Mint a new token even if one already exists for this account.</p>
          </div>
          <Switch
            id="issue-force"
            checked={Boolean(form.force)}
            onCheckedChange={(checked) => updateField('force', checked)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="issue-reason">Reason</Label>
          <Textarea
            id="issue-reason"
            placeholder="Explain why this automation token is needed."
            value={form.reason}
            onChange={(event) => updateField('reason', event.target.value)}
          />
          <p className="text-xs text-foreground/60">Minimum 10 characters. Displayed in audit logs.</p>
        </div>
        {form.mode === 'vault' ? (
          <div className="space-y-4 rounded-lg border border-white/10 p-3">
            <p className="text-sm text-foreground/70">
              Provide the Vault headers captured from the Starter CLI or your Vault workflow. These are forwarded verbatim
              to the FastAPI `/service-accounts/issue` endpoint.
            </p>
            <div className="space-y-2">
              <Label htmlFor="issue-vault-authorization">Vault Authorization header</Label>
              <Input
                id="issue-vault-authorization"
                placeholder="vault:v1:transit/..."
                value={form.vaultAuthorization ?? ''}
                onChange={(event) => updateField('vaultAuthorization', event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="issue-vault-payload">Vault payload (base64)</Label>
              <Textarea
                id="issue-vault-payload"
                placeholder="Base64 payload emitted by Vault transit sign"
                value={form.vaultPayload ?? ''}
                onChange={(event) => updateField('vaultPayload', event.target.value)}
                rows={3}
              />
              <p className="text-xs text-foreground/60">Optional for dev-local mode. Required when sending real Vault signatures.</p>
            </div>
          </div>
        ) : null}
        {formError ? (
          <p className="text-sm font-medium text-destructive" role="alert">
            {formError}
          </p>
        ) : null}
      </div>
      <DialogFooter>
        <Button type="button" variant="ghost" onClick={onDismiss} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Issuing…' : 'Issue token'}
        </Button>
      </DialogFooter>
    </form>
  );

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-lg">
        {issuedToken ? (
          <IssuedTokenView token={issuedToken} onDone={onDismiss} onIssueAnother={onIssueAnother} />
        ) : (
          renderForm()
        )}
      </DialogContent>
    </Dialog>
  );
}

interface IssuedTokenViewProps {
  token: ServiceAccountIssueResult;
  onDone: () => void;
  onIssueAnother: () => void;
}

function IssuedTokenView({ token, onDone, onIssueAnother }: IssuedTokenViewProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(token.refreshToken);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      setCopied(false);
    }
  };

  return (
    <div className="space-y-4">
      <DialogHeader>
        <DialogTitle>Copy your token now</DialogTitle>
        <DialogDescription>This refresh token is only shown once. Store it in your secret manager.</DialogDescription>
      </DialogHeader>
      <div className="space-y-3">
        <Textarea readOnly value={token.refreshToken} className="font-mono text-sm" rows={4} />
        <Button type="button" variant="outline" onClick={handleCopy}>
          {copied ? 'Copied!' : 'Copy token'}
        </Button>
      </div>
      <div className="rounded-lg border border-white/10 p-3 text-sm text-foreground/70">
        <p className="font-medium text-foreground">Details</p>
        <ul className="mt-2 space-y-1">
          <li>
            <span className="text-foreground/60">Account:</span> {token.account}
          </li>
          <li>
            <span className="text-foreground/60">Scopes:</span> {token.scopes.join(', ')}
          </li>
          <li>
            <span className="text-foreground/60">Expires:</span> {formatDate(token.expiresAt)}
          </li>
        </ul>
      </div>
      <DialogFooter className="flex flex-wrap gap-2">
        <Button type="button" variant="secondary" onClick={onIssueAnother}>
          Issue another
        </Button>
        <Button type="button" onClick={onDone}>
          Done
        </Button>
      </DialogFooter>
    </div>
  );
}
