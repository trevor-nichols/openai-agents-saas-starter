import { GlassPanel } from '@/components/ui/foundation/GlassPanel';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

type ErrorStateVariant = 'default' | 'card';

interface ErrorStateProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  message?: string;
  onRetry?: () => void;
  action?: React.ReactNode;
  variant?: ErrorStateVariant;
}

export function ErrorState({
  title = 'Something went wrong',
  message,
  onRetry,
  action,
  variant = 'default',
  className,
  ...props
}: ErrorStateProps) {
  const actionNode = action ?? (onRetry ? <Button onClick={onRetry}>Try again</Button> : null);
  const Container = variant === 'card' ? GlassPanel : 'div';
  const containerClass = cn(
    'text-center',
    variant === 'default' && 'bg-transparent p-0 shadow-none',
    className,
  );

  return (
    <Container className={containerClass} {...props}>
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full border border-destructive/30 bg-destructive/15 text-2xl text-destructive">
        !
      </div>
      <h3 className="mt-6 text-xl font-semibold tracking-tight">{title}</h3>
      {message ? <p className="mt-2 text-sm text-foreground/70">{message}</p> : null}
      {actionNode ? <div className="mt-6 flex justify-center">{actionNode}</div> : null}
    </Container>
  );
}
