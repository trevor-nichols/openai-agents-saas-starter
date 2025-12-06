import { cn } from '@/lib/utils';
import { ArrowDownIcon, ArrowRightIcon, ArrowUpIcon } from 'lucide-react';

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
  positive: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400',
  negative: 'bg-rose-500/15 text-rose-600 dark:text-rose-400',
  neutral: 'bg-muted text-muted-foreground',
};

const toneIcons: Record<StatTone, React.ReactNode> = {
  positive: <ArrowUpIcon className="mr-1 h-3 w-3" />,
  negative: <ArrowDownIcon className="mr-1 h-3 w-3" />,
  neutral: <ArrowRightIcon className="mr-1 h-3 w-3" />,
};

export function StatCard({ label, value, helperText, icon, trend, className, ...props }: StatCardProps) {
  return (
    <div className={cn('flex flex-col justify-between rounded-3xl border bg-card p-6 shadow-sm transition-all hover:shadow-md', className)} {...props}>
      <div className="flex items-start justify-between">
        <p className="text-sm font-medium text-muted-foreground">{label}</p>
        {icon ? (
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary">
            {icon}
          </div>
        ) : null}
      </div>

      <div className="mt-4">
        <div className="text-4xl font-bold tracking-tight text-foreground">{value}</div>
        <div className="mt-1 flex items-center gap-2">
          {trend ? (
            <div className={cn('inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium', toneStyles[trend.tone ?? 'neutral'])}>
              {toneIcons[trend.tone ?? 'neutral']}
              {trend.value}
            </div>
          ) : null}
          {trend?.label ? <p className="text-xs text-muted-foreground">{trend.label}</p> : null}
          {helperText && !trend ? <p className="text-xs text-muted-foreground">{helperText}</p> : null}
        </div>
      </div>
    </div>
  );
}
