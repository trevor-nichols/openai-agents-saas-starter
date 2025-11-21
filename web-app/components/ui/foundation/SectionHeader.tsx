import { cn } from '@/lib/utils';

interface SectionHeaderProps {
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
        'flex flex-col sm:flex-row sm:items-end sm:justify-between',
        isCompact ? 'gap-2' : 'gap-3',
        className,
      )}
    >
      <div>
        {eyebrow ? (
          <p className={cn('font-semibold uppercase tracking-[0.3em] text-foreground/50', isCompact ? 'text-[11px]' : 'text-xs')}>
            {eyebrow}
          </p>
        ) : null}
        <div className={cn(isCompact ? 'mt-0.5' : 'mt-1')}>
          <h2 className={cn('font-semibold tracking-tight text-foreground', isCompact ? 'text-lg' : 'text-xl')}>
            {title}
          </h2>
          {description ? (
            <p className={cn('text-foreground/70', isCompact ? 'mt-0.5 text-sm' : 'mt-1 text-sm')}>
              {description}
            </p>
          ) : null}
        </div>
      </div>
      {actions ? <div className="flex flex-shrink-0 items-center gap-2">{actions}</div> : null}
    </div>
  );
}
