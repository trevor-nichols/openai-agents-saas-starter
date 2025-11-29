import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { SectionHeader } from '@/components/ui/foundation';

import type { MarketingFaqItem } from '@/features/marketing/types';

interface FaqSectionProps {
  items: MarketingFaqItem[];
  title?: string;
  description?: string;
  eyebrow?: string;
}

export function FaqSection({ items, title = 'Answers for builders and operators', description, eyebrow = 'FAQ' }: FaqSectionProps) {
  return (
    <section className="space-y-6">
      <SectionHeader
        eyebrow={eyebrow}
        title={title}
        description={description ?? 'If you do not see your question here, reach out via the contact CTA and we will get you unblocked.'}
      />
      <Accordion type="single" collapsible>
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
