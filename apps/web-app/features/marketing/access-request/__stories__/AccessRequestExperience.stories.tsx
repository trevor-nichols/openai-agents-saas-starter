'use client';

import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';

import { AccessRequestExperience } from '../AccessRequestExperience';
import { SubmissionSuccess } from '../components/SubmissionSuccess';
import type { AccessRequestSubmission } from '../types';

function AccessRequestExperiencePreview() {
  const [submission, setSubmission] = useState<AccessRequestSubmission | null>(null);

  if (submission) {
    return <SubmissionSuccess submission={submission} onReset={() => setSubmission(null)} />;
  }

  return (
    <AccessRequestExperience />
  );
}

const meta: Meta<typeof AccessRequestExperiencePreview> = {
  title: 'Marketing/Access Request/Page',
  component: AccessRequestExperiencePreview,
};

export default meta;

type Story = StoryObj<typeof AccessRequestExperiencePreview>;

export const Default: Story = {};
