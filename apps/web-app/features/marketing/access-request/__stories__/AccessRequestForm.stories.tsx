'use client';

import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';

import { AccessRequestForm } from '../components/AccessRequestForm';
import { SubmissionSuccess } from '../components/SubmissionSuccess';
import type { AccessRequestSubmission } from '../types';

function AccessRequestFormPreview() {
  const [submission, setSubmission] = useState<AccessRequestSubmission | null>(null);

  if (submission) {
    return <SubmissionSuccess submission={submission} onReset={() => setSubmission(null)} />;
  }

  return (
    <AccessRequestForm
      onSubmitted={(payload) => {
        setSubmission(payload);
      }}
    />
  );
}

const meta: Meta<typeof AccessRequestFormPreview> = {
  title: 'Marketing/Access Request/Form',
  component: AccessRequestFormPreview,
};

export default meta;

type Story = StoryObj<typeof AccessRequestFormPreview>;

export const Default: Story = {};
