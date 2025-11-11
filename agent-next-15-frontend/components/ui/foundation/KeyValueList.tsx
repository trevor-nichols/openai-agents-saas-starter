import { cn } from '@/lib/utils';

interface KeyValueItem {
  label: string;
  value: React.ReactNode;
  hint?: string;
}

interface KeyValueListProps {
  items: KeyValueItem[];
  columns?: 1 | 2;
  className?: string;
}

export function KeyValueList({ items, columns = 1, className }: KeyValueListProps) {
  return (
    <dl
      className={cn(
        'grid gap-4 text-sm text-foreground/80',
        columns === 2 ? 'md:grid-cols-2' : 'grid-cols-1',
        className
      )}
    >
      {items.map((item) => (
        <div key={item.label} className="flex flex-col gap-1 rounded-lg border border-white/5 bg-white/5 px-4 py-3">
          <dt className="text-xs uppercase tracking-[0.25em] text-foreground/50">{item.label}</dt>
          <dd className="text-base text-foreground">{item.value}</dd>
          {item.hint ? <p className="text-xs text-foreground/50">{item.hint}</p> : null}
        </div>
      ))}
    </dl>
  );
}
