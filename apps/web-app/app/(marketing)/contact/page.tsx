import { StaticPage, CONTACT_PAGE, ContactForm } from '@/features/marketing/static-pages';

export const metadata = {
  title: 'Contact | AI Agent SaaS Starter',
  description: CONTACT_PAGE.description,
};

export default function ContactPage() {
  return (
    <div className="space-y-10">
      <StaticPage content={CONTACT_PAGE} />
      <ContactForm />
    </div>
  );
}
