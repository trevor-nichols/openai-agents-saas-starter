import { cn } from '@/lib/utils';

interface SectionHeaderProps {
  title: string;
  description?: string;
  eyebrow?: string;
  actions?: React.ReactNode;
  className?: string;
}

export function SectionHeader({ title, description, eyebrow, actions, className }: SectionHeaderProps) {
  return (
    <div className={cn('flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between', className)}>
      <div>
        {eyebrow ? <p className="text-xs font-semibold uppercase tracking-[0.3em] text-foreground/50">{eyebrow}</p> : null}
        <div className="mt-1">
          <h2 className="text-xl font-semibold tracking-tight text-foreground">{title}</h2>
          {description ? <p className="mt-1 text-sm text-foreground/70">{description}</p> : null}
        </div>
      </div>
      {actions ? <div className="flex flex-shrink-0 items-center gap-2">{actions}</div> : null}
    </div>
  );
}
