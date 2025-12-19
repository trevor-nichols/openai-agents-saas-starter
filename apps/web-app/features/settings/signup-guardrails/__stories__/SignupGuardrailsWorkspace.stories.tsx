'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { SignupGuardrailsWorkspace } from '../SignupGuardrailsWorkspace';

const meta: Meta<typeof SignupGuardrailsWorkspace> = {
  title: 'Settings/Signup Guardrails/Workspace',
  component: SignupGuardrailsWorkspace,
};

export default meta;

type Story = StoryObj<typeof SignupGuardrailsWorkspace>;

export const Default: Story = {};
