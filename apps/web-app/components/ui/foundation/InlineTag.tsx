import { cn } from '@/lib/utils';

type InlineTagTone = 'default' | 'positive' | 'warning';

interface InlineTagProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: InlineTagTone;
  icon?: React.ReactNode;
}

const toneClassMap: Record<InlineTagTone, string> = {
  default: 'bg-muted/50 text-muted-foreground border-transparent',
  positive: 'bg-emerald-500/15 text-emerald-500 border-emerald-500/20',
  warning: 'bg-amber-500/15 text-amber-500 border-amber-500/20',
};

export function InlineTag({ children, tone = 'default', icon, className, ...props }: InlineTagProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors',
        toneClassMap[tone],
        className
      )}
      {...props}
    >
      {icon ? <span className="flex shrink-0 items-center justify-center [&>svg]:size-3">{icon}</span> : null}
      {children}
    </span>
  );
}
