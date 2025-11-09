import { LoginForm } from '@/components/auth/LoginForm';

interface LoginPageProps {
  searchParams?: Record<string, string | string[] | undefined>;
}

export default function LoginPage({ searchParams }: LoginPageProps) {
  const redirectTo = typeof searchParams?.redirectTo === 'string' ? searchParams?.redirectTo : undefined;

  return (
    <main className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-semibold text-gray-900">Sign in to Anything Agents</h1>
          <p className="text-sm text-gray-500">Use your organization credentials to continue.</p>
        </div>
        <LoginForm redirectTo={redirectTo} />
      </div>
    </main>
  );
}
