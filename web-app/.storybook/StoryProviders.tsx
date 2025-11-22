import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { Geist, Geist_Mono } from 'next/font/google';
import { ThemeProvider } from 'next-themes';

import '../app/globals.css';
import { Toaster } from '../components/ui/sonner';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
  display: 'swap',
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
  display: 'swap',
});

export const StoryProviders = ({ children, theme }: { children: ReactNode; theme: string }) => {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      })
  );

  const forcedTheme = useMemo(() => (theme === 'system' ? undefined : theme), [theme]);

  useEffect(() => {
    document.body.classList.add(geistSans.variable, geistMono.variable);
    return () => {
      document.body.classList.remove(geistSans.variable, geistMono.variable);
    };
  }, []);

  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem forcedTheme={forcedTheme} disableTransitionOnChange>
      <QueryClientProvider client={queryClient}>
        <div className="min-h-screen bg-background text-foreground antialiased">
          {children}
          <Toaster richColors position="top-center" />
        </div>
      </QueryClientProvider>
    </ThemeProvider>
  );
};
