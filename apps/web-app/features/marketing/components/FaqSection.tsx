import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { SectionHeader } from '@/components/ui/foundation';

import type { MarketingFaqItem } from '@/features/marketing/types';

interface FaqSectionProps {
  items: MarketingFaqItem[];
  title?: string;
  description?: string;
  eyebrow?: string;
  columns?: 1 | 2;
}

export function FaqSection({ items, title = 'Answers for builders and operators', description, eyebrow = 'FAQ', columns = 1 }: FaqSectionProps) {
  const accordionClassName = columns === 2 ? 'grid gap-4 md:grid-cols-2' : undefined;

  return (
    <section className="space-y-6">
      <SectionHeader
        eyebrow={eyebrow}
        title={title}
        description={description ?? 'If you do not see your question here, reach out via the contact CTA and we will get you unblocked.'}
      />
      <Accordion type="single" collapsible className={accordionClassName}>
        {items.map((item) => (
          <AccordionItem key={item.question} value={item.question}>
            <AccordionTrigger>{item.question}</AccordionTrigger>
            <AccordionContent>
              <p className="text-sm text-foreground/70">{item.answer}</p>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </section>
  );
}
