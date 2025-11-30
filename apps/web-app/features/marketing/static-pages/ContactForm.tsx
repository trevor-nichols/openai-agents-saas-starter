"use client";

import { FormEvent, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/use-toast';
import { GlassPanel, SectionHeader } from '@/components/ui/foundation';
import { useSubmitContactMutation } from '@/lib/queries/marketing';

export function ContactForm() {
  const toast = useToast();
  const submitMutation = useSubmitContactMutation();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [company, setCompany] = useState('');
  const [topic, setTopic] = useState('');
  const [message, setMessage] = useState('');
  const [honeypot, setHoneypot] = useState('');

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!email.trim() || !message.trim()) {
      toast.error({ title: 'Missing info', description: 'Please add your email and a short message.' });
      return;
    }

    submitMutation.mutate(
      {
        name,
        email,
        company,
        topic,
        message,
        honeypot,
      },
      {
        onSuccess: () => {
          toast.success({ title: 'Message sent', description: 'Thanks for reaching out. We will reply shortly.' });
          setName('');
          setEmail('');
          setCompany('');
          setTopic('');
          setMessage('');
          setHoneypot('');
        },
        onError: (error) => {
          toast.error({ title: 'Unable to send', description: error.message });
        },
      },
    );
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
          {/* Honeypot field for spam bots */}
          <input
            type="text"
            tabIndex={-1}
            autoComplete="off"
            value={honeypot}
            onChange={(e) => setHoneypot(e.target.value)}
            className="hidden"
            aria-hidden="true"
          />
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
          <Input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Topic (optional)"
            aria-label="Topic"
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
            <Button type="submit" disabled={submitMutation.isPending}>
              {submitMutation.isPending ? 'Sending…' : 'Send message'}
            </Button>
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
