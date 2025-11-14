import { GlassPanel } from '@/components/ui/foundation/GlassPanel';
import { cn } from '@/lib/utils';

interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}

export function EmptyState({ title, description, icon, action, className, ...props }: EmptyStateProps) {
  return (
    <GlassPanel className={cn('text-center', className)} {...props}>
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full border border-white/10 bg-white/5 text-2xl text-foreground/70">
        {icon ?? '◦'}
      </div>
      <h3 className="mt-6 text-xl font-semibold tracking-tight">{title}</h3>
      {description ? <p className="mt-2 text-sm text-foreground/70">{description}</p> : null}
      {action ? <div className="mt-6 flex justify-center">{action}</div> : null}
    </GlassPanel>
  );
}
