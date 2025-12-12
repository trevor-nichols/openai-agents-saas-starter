import { GlassPanel } from '@/components/ui/foundation/GlassPanel';
import { cn } from '@/lib/utils';

type EmptyStateVariant = 'default' | 'card';

interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  variant?: EmptyStateVariant;
}

export function EmptyState({
  title,
  description,
  icon,
  action,
  variant = 'default',
  className,
  ...props
}: EmptyStateProps) {
  const Container = variant === 'card' ? GlassPanel : 'div';
  const containerClass = cn(
    'text-center',
    variant === 'default' && 'bg-transparent p-0 shadow-none',
    className,
  );

  const iconClass = cn(
    'mx-auto flex h-14 w-14 items-center justify-center rounded-full text-2xl text-foreground/70',
    variant === 'default' ? 'bg-transparent' : 'border border-white/10 bg-white/5',
  );

  return (
    <Container className={containerClass} {...props}>
      <div className={iconClass}>{icon ?? '◦'}</div>
      <h3 className="mt-6 text-xl font-semibold tracking-tight">{title}</h3>
      {description ? <p className="mt-2 text-sm text-foreground/70">{description}</p> : null}
      {action ? <div className="mt-6 flex justify-center">{action}</div> : null}
    </Container>
  );
}
