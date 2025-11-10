// File Path: app/(app)/account/profile/page.tsx
// Description: Placeholder user profile page.
// Sections:
// - ProfilePage component: Stub content for profile details and verification status.

export const metadata = {
  title: 'Profile | Anything Agents',
};

export default function ProfilePage() {
  return (
    <section className="space-y-4">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-slate-900">Profile</h1>
        <p className="text-sm text-slate-500">
          Display user metadata, tenant info, and email verification status sourced from the session APIs.
        </p>
      </header>

      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
        Profile details placeholder. Integrate session service to populate this card.
      </div>
    </section>
  );
}

