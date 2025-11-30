import { StaticPage, PRIVACY_PAGE } from '@/features/marketing/static-pages';

export const metadata = {
  title: 'Privacy | AI Agent SaaS Starter',
  description: PRIVACY_PAGE.description,
};

export default function PrivacyPage() {
  return <StaticPage content={PRIVACY_PAGE} />;
}
