import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { RevokeTokenDialog } from '../components/RevokeTokenDialog';
import { IssueTokenDialog } from '../components/IssueTokenDialog';
import { createDefaultIssueForm } from '../utils/issueForm';
import type { ServiceAccountIssueFormValues } from '../utils/issueForm';
import type { ServiceAccountIssueResult, ServiceAccountTokenRow } from '@/types/serviceAccounts';

const sampleToken: ServiceAccountTokenRow = {
  id: 'token-1',
  account: 'ci-runner',
  tenantId: 'tenant-1',
  scopes: ['conversations:read'],
  issuedAt: new Date().toISOString(),
  expiresAt: new Date(Date.now() + 86_400_000).toISOString(),
  revokedAt: null,
  signingKeyId: 'kid-1',
  fingerprint: 'runner-1',
  revokedReason: null,
};

const sampleIssueResult: ServiceAccountIssueResult = {
  refreshToken: 'rt-token',
  account: 'ci-runner',
  tenantId: 'tenant-1',
  scopes: ['conversations:read'],
  expiresAt: new Date(Date.now() + 86_400_000).toISOString(),
  issuedAt: new Date().toISOString(),
  kid: 'kid-1',
  tokenUse: 'refresh',
};

describe('RevokeTokenDialog', () => {
  it('calls onConfirm when revoke is clicked', async () => {
    const onConfirm = vi.fn();

    render(
      <RevokeTokenDialog
        token={sampleToken}
        reason=""
        onReasonChange={() => {}}
        onConfirm={onConfirm}
        onClose={() => {}}
        isSubmitting={false}
      />,
    );

    fireEvent.click(screen.getByText('Revoke token'));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('propagates reason changes', async () => {
    const onReasonChange = vi.fn();

    render(
      <RevokeTokenDialog
        token={sampleToken}
        reason=""
        onReasonChange={onReasonChange}
        onConfirm={() => {}}
        onClose={() => {}}
        isSubmitting={false}
      />,
    );

    const textarea = screen.getByPlaceholderText('Optional reason (shown in audit logs)');
    fireEvent.change(textarea, { target: { value: 'rotating credentials' } });

    expect(onReasonChange).toHaveBeenCalled();
    expect(onReasonChange).toHaveBeenLastCalledWith('rotating credentials');
  });
});

describe('IssueTokenDialog', () => {
  const baseForm: ServiceAccountIssueFormValues = createDefaultIssueForm('tenant-1');

  it('submits the issue form', async () => {
    const onSubmit = vi.fn();

    render(
      <IssueTokenDialog
        open
        form={baseForm}
        onFormChange={() => {}}
        issuedToken={null}
        isSubmitting={false}
        formError={null}
        onSubmit={onSubmit}
        onDismiss={() => {}}
        onIssueAnother={() => {}}
      />,
    );

    fireEvent.click(screen.getByText('Issue token'));
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it('renders issued token view', () => {
    render(
      <IssueTokenDialog
        open
        form={baseForm}
        onFormChange={() => {}}
        issuedToken={sampleIssueResult}
        isSubmitting={false}
        formError={null}
        onSubmit={() => {}}
        onDismiss={() => {}}
        onIssueAnother={() => {}}
      />,
    );

    expect(screen.getByText('Copy your token now')).toBeInTheDocument();
    expect(screen.getByText(sampleIssueResult.refreshToken)).toBeInTheDocument();
  });
});
