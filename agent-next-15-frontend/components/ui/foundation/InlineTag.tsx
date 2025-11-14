import { cn } from '@/lib/utils';

type InlineTagTone = 'default' | 'positive' | 'warning';

interface InlineTagProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: InlineTagTone;
  icon?: React.ReactNode;
}

const toneClassMap: Record<InlineTagTone, string> = {
  default: 'border-white/15 bg-white/5 text-foreground/80',
  positive: 'border-success/40 bg-success/10 text-success',
  warning: 'border-warning/40 bg-warning/10 text-warning',
};

export function InlineTag({ children, tone = 'default', icon, className, ...props }: InlineTagProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-pill border px-3 py-1 text-xs font-semibold uppercase tracking-wide',
        toneClassMap[tone],
        className
      )}
      {...props}
    >
      {icon ? <span className="text-base leading-none">{icon}</span> : null}
      {children}
    </span>
  );
}
