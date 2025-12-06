import { StaticPage, ABOUT_PAGE } from '@/features/marketing/static-pages';

export const metadata = {
  title: 'About | AI Agent SaaS Starter',
  description: ABOUT_PAGE.description,
};

export default function AboutPage() {
  return <StaticPage content={ABOUT_PAGE} />;
}
