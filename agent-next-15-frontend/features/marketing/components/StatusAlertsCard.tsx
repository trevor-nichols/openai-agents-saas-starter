'use client';

import { FormEvent, useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { GlassPanel, SectionHeader } from '@/components/ui/foundation';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/components/ui/use-toast';
import { useStatusSubscriptionMutation } from '@/lib/queries/statusSubscriptions';

interface StatusAlertsCardProps {
  onLeadSubmit: (params: { location: string; channel: 'email'; severity: string; emailDomain?: string }) => void;
  source?: string;
}

const SEVERITY_OPTIONS = [
  { value: 'major', label: 'Major incidents' },
  { value: 'all', label: 'All incidents' },
  { value: 'maintenance', label: 'Maintenance windows' },
];

export function StatusAlertsCard({ onLeadSubmit, source = 'status-alert-card' }: StatusAlertsCardProps) {
  const [email, setEmail] = useState('');
  const [severity, setSeverity] = useState('major');
  const toast = useToast();
  const subscription = useStatusSubscriptionMutation();

  const emailDomain = useMemo(() => {
    const [, domain] = email.split('@');
    return domain?.toLowerCase();
  }, [email]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!email) {
      toast.error({ title: 'Email required', description: 'Enter an email to receive alerts.' });
      return;
    }

    try {
      await subscription.mutateAsync({
        channel: 'email',
        target: email,
        severity_filter: severity as 'all' | 'major' | 'maintenance',
        metadata: { source },
      });
      toast.success({
        title: 'Check your inbox',
        description: 'We sent a verification email to confirm your subscription.',
      });
      onLeadSubmit({ location: `${source}:submit`, channel: 'email', severity, emailDomain });
      setEmail('');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to subscribe right now.';
      toast.error({ title: 'Subscription failed', description: message });
    }
  };

  return (
    <GlassPanel className="space-y-6">
      <SectionHeader
        eyebrow="Status alerts"
        title="Subscribe to incident updates"
        description="Opt into email updates so your team knows when incidents or maintenance windows land."
      />
      <form className="space-y-4" onSubmit={handleSubmit}>
        <div className="grid gap-4 md:grid-cols-[2fr,1fr]">
          <Input
            type="email"
            placeholder="you@company.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
            aria-label="Email address"
          />
          <Select value={severity} onValueChange={setSeverity}>
            <SelectTrigger aria-label="Severity filter">
              <SelectValue placeholder="Select severity" />
            </SelectTrigger>
            <SelectContent>
              {SEVERITY_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Button type="submit" disabled={subscription.isPending}>
          {subscription.isPending ? 'Subscribing…' : 'Subscribe for alerts'}
        </Button>
      </form>
    </GlassPanel>
  );
}
