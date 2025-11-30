"use client";

import { FormEvent, useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/use-toast';
import { GlassPanel, SectionHeader } from '@/components/ui/foundation';

const DEFAULT_TO = 'support@yourcompany.com';

export function ContactForm() {
  const toast = useToast();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [company, setCompany] = useState('');
  const [message, setMessage] = useState('');

  const mailtoHref = useMemo(() => {
    const subject = encodeURIComponent('Contact: AI Agent Starter');
    const body = encodeURIComponent(
      `Name: ${name}\nEmail: ${email}\nCompany: ${company}\n\nMessage:\n${message}`,
    );
    return `mailto:${DEFAULT_TO}?subject=${subject}&body=${body}`;
  }, [name, email, company, message]);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!email || !message) {
      toast.error({ title: 'Missing info', description: 'Please add your email and a short message.' });
      return;
    }
    toast.success({ title: 'Opening your email client', description: 'Review and send the prefilled message.' });
    window.location.href = mailtoHref;
  };

  return (
    <div className="mx-auto w-full max-w-4xl">
      <GlassPanel className="space-y-6 border border-white/10">
        <SectionHeader
          eyebrow="Contact"
          title="Send us a note"
          description="Tell us what you are building and how we can help wire the starter."
        />
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="grid gap-4 md:grid-cols-2">
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Full name"
              aria-label="Full name"
            />
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Email"
              aria-label="Email"
              required
            />
          </div>
          <Input
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            placeholder="Company (optional)"
            aria-label="Company"
          />
          <Textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="What are you trying to ship?"
            aria-label="Message"
            rows={5}
            required
          />
          <div className="flex flex-wrap gap-3">
            <Button type="submit">Send via email</Button>
            <Button type="button" variant="secondary" asChild>
              <a href="https://calendly.com/your-team/intro" target="_blank" rel="noreferrer">
                Book a 15-min call
              </a>
            </Button>
          </div>
        </form>
      </GlassPanel>
    </div>
  );
}
