import { StaticPage, TERMS_PAGE } from '@/features/marketing/static-pages';

export const metadata = {
  title: 'Terms | AI Agent SaaS Starter',
  description: TERMS_PAGE.description,
};

export default function TermsPage() {
  return <StaticPage content={TERMS_PAGE} />;
}
