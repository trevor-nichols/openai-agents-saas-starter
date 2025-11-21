import { GlassPanel } from '@/components/ui/foundation/GlassPanel';
import { cn } from '@/lib/utils';

type StatTone = 'positive' | 'negative' | 'neutral';

interface StatCardProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string;
  value: React.ReactNode;
  helperText?: string;
  icon?: React.ReactNode;
  trend?: {
    value: string;
    tone?: StatTone;
    label?: string;
  };
}

const toneStyles: Record<StatTone, string> = {
  positive: 'text-success',
  negative: 'text-destructive',
  neutral: 'text-foreground/60',
};

export function StatCard({ label, value, helperText, icon, trend, className, ...props }: StatCardProps) {
  return (
    <GlassPanel className={cn('flex flex-col gap-4', className)} {...props}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-foreground/50">{label}</p>
        </div>
        {icon ? <div className="rounded-pill border border-white/10 bg-white/5 p-2 text-foreground/80">{icon}</div> : null}
      </div>

      <div className="flex flex-wrap items-end justify-between gap-2">
        <div className="text-3xl font-semibold tracking-tight text-foreground">{value}</div>
        {trend ? (
          <div className="text-right text-sm">
            <p className={cn('font-semibold', toneStyles[trend.tone ?? 'neutral'])}>{trend.value}</p>
            {trend.label ? <p className="text-foreground/50">{trend.label}</p> : null}
          </div>
        ) : null}
      </div>

      {helperText ? <p className="text-sm text-foreground/60">{helperText}</p> : null}
    </GlassPanel>
  );
}
