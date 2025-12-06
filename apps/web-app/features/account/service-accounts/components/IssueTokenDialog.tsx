'use client';

import { FormEvent, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import type { ServiceAccountIssueResult } from '@/types/serviceAccounts';

import type { ServiceAccountIssueFormValues } from '../utils/issueForm';
import { formatDate } from '../utils/display';

interface IssueTokenDialogProps {
  open: boolean;
  form: ServiceAccountIssueFormValues;
  onFormChange: (updater: (current: ServiceAccountIssueFormValues) => ServiceAccountIssueFormValues) => void;
  issuedToken: ServiceAccountIssueResult | null;
  isSubmitting: boolean;
  formError: string | null;
  onSubmit: () => void | Promise<void>;
  onDismiss: () => void;
  onIssueAnother: () => void;
}

export function IssueTokenDialog({
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
            Browser mode signs on your behalf. Vault mode forwards the Vault Authorization + payload headers that you capture from Vault Transit or the Starter CLI.
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
              onChange={(event) => updateField('lifetimeMinutes', event.target.value ? Number(event.target.value) : undefined)}
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
          <Switch id="issue-force" checked={Boolean(form.force)} onCheckedChange={(checked) => updateField('force', checked)} />
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
              Provide the Vault headers captured from the Starter CLI or your Vault workflow. These are forwarded verbatim to the FastAPI `/service-accounts/issue` endpoint.
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
        {issuedToken ? <IssuedTokenView token={issuedToken} onDone={onDismiss} onIssueAnother={onIssueAnother} /> : renderForm()}
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
    } catch (_error) {
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
