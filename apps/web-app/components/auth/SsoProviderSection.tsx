import type { ComponentType } from 'react';
import type { IconType } from '@icons-pack/react-simple-icons';
import { SiGoogle } from '@icons-pack/react-simple-icons';
import { LogIn } from 'lucide-react';

import type { SsoProviderView } from '@/lib/api/client/types.gen';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Spinner } from '@/components/ui/spinner';
import { cn } from '@/lib/utils';

type ProviderIcon = ComponentType<{ className?: string; size?: number }>;

const providerIconMap: Record<string, IconType> = {
  google: SiGoogle,
};

const DefaultIcon: ProviderIcon = LogIn;

interface SsoProviderSectionProps {
  hasTenantSelection: boolean;
  providers: SsoProviderView[];
  isLoading: boolean;
  error?: string | null;
  activeProvider?: string | null;
  onSelect: (provider: SsoProviderView) => void;
}

export function SsoProviderSection({
  hasTenantSelection,
  providers,
  isLoading,
  error,
  activeProvider,
  onSelect,
}: SsoProviderSectionProps) {
  if (!hasTenantSelection) {
    return (
      <p className="text-xs text-muted-foreground">
        Enter a tenant slug or ID to reveal available SSO options.
      </p>
    );
  }

  const hasProviders = providers.length > 0;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Separator className="flex-1" />
        <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Or continue with
        </span>
        <Separator className="flex-1" />
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
          <Spinner className="h-4 w-4" />
          Loading providers…
        </div>
      ) : hasProviders ? (
        <div className="space-y-2">
          {providers.map((provider) => {
            const Icon = (providerIconMap[provider.provider_key] ?? DefaultIcon) as ProviderIcon;
            const isActive = activeProvider === provider.provider_key;
            return (
              <Button
                key={provider.provider_key}
                type="button"
                variant="outline"
                className={cn('w-full justify-center gap-2', isActive && 'cursor-wait')}
                onClick={() => onSelect(provider)}
                disabled={isLoading || Boolean(activeProvider)}
              >
                {isActive ? <Spinner className="h-4 w-4" /> : <Icon className="h-4 w-4" />}
                Continue with {provider.display_name}
              </Button>
            );
          })}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">
          No SSO providers are configured for this tenant yet.
        </p>
      )}

      {error ? <p className="text-sm text-destructive">{error}</p> : null}
    </div>
  );
}
