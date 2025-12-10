import type { ConversationHistory } from '@/types/conversations';

const now = Date.now();

export const conversationDetailFixture: ConversationHistory = {
  conversation_id: 'conv_12345',
  display_name: 'Billing dispute follow-up',
  created_at: new Date(now - 1000 * 60 * 60 * 24).toISOString(),
  updated_at: new Date(now - 1000 * 60 * 10).toISOString(),
  agent_context: {
    agent: 'billing-escalation',
    run_id: 'run_987',
    customer_tier: 'enterprise',
    region: 'us-east',
  },
  messages: [
    {
      role: 'user',
      content: "I'm seeing a duplicate charge for September.",
      timestamp: new Date(now - 1000 * 60 * 55).toISOString(),
    },
    {
      role: 'assistant',
      content: 'I can help check that. Do you have the invoice ID?',
      timestamp: new Date(now - 1000 * 60 * 54).toISOString(),
    },
    {
      role: 'user',
      content: 'Invoice INV-2045 is duplicated.',
      timestamp: new Date(now - 1000 * 60 * 52).toISOString(),
    },
    {
      role: 'assistant',
      content: 'Confirmed the duplicate. I will refund the extra charge and email you a confirmation.',
      timestamp: new Date(now - 1000 * 60 * 50).toISOString(),
    },
  ],
};
