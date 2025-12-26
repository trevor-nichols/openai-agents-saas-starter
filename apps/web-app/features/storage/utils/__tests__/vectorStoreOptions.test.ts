import { describe, expect, it } from 'vitest';

import { buildAgentOptions, buildConversationOptions } from '../vectorStoreOptions';

describe('vectorStoreOptions', () => {
  it('builds agent options with display name fallback', () => {
    const options = buildAgentOptions([
      { name: 'alpha', display_name: 'Alpha Agent', description: 'Primary agent' },
      { name: 'beta', display_name: null, description: null },
    ]);

    expect(options).toEqual([
      { value: 'alpha', label: 'Alpha Agent', description: 'Primary agent' },
      { value: 'beta', label: 'beta', description: null },
    ]);
  });

  it('builds conversation options with layered label fallback', () => {
    const options = buildConversationOptions([
      {
        id: 'abc12345',
        display_name: 'Synthesis',
        title: 'Ignored title',
        last_message_preview: 'Ignored preview',
      },
      {
        id: 'def67890',
        display_name: null,
        title: 'Workspace',
        last_message_preview: 'Preview for workspace',
      },
      {
        id: 'ghi',
        display_name: null,
        title: null,
        last_message_preview: 'Recent message',
      },
      {
        id: 'xyz',
        display_name: null,
        title: null,
        last_message_preview: null,
      },
    ]);

    expect(options).toEqual([
      { value: 'abc12345', label: 'Synthesis', description: 'Ignored preview' },
      { value: 'def67890', label: 'Workspace', description: 'Preview for workspace' },
      { value: 'ghi', label: 'Recent message', description: 'Recent message' },
      { value: 'xyz', label: 'Conversation xyz', description: null },
    ]);
  });
});
