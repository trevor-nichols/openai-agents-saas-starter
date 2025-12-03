import { cn } from '@/lib/utils';

export interface SectionHeaderProps {
  title: string;
  description?: string;
  eyebrow?: string;
  actions?: React.ReactNode;
  className?: string;
  size?: 'default' | 'compact';
}

export function SectionHeader({ title, description, eyebrow, actions, className, size = 'default' }: SectionHeaderProps) {
  const isCompact = size === 'compact';

  return (
    <div
      className={cn(
        'flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between',
        className,
      )}
    >
      <div className="space-y-1.5">
        {eyebrow ? (
          <p className="text-xs font-medium uppercase tracking-wider text-primary">
            {eyebrow}
          </p>
        ) : null}
        <div className="space-y-1">
          <h2 className={cn('font-bold tracking-tight text-foreground', isCompact ? 'text-xl' : 'text-3xl')}>
            {title}
          </h2>
          {description ? (
            <p className={cn('text-muted-foreground max-w-3xl', isCompact ? 'text-sm' : 'text-base')}>
              {description}
            </p>
          ) : null}
        </div>
      </div>
      {actions ? <div className={cn("flex flex-shrink-0 items-center gap-2", isCompact ? "" : "sm:pt-1")}>{actions}</div> : null}
    </div>
  );
}
