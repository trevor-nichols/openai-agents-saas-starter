import { SettingsNav } from './_components/SettingsNav';

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid gap-8 lg:grid-cols-[240px_minmax(0,1fr)]">
      <SettingsNav />
      <div className="min-w-0">{children}</div>
    </div>
  );
}
