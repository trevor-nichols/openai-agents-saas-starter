import { cn } from '@/lib/utils';

interface PasswordPolicyListProps {
  items: readonly string[];
  className?: string;
}

export function PasswordPolicyList({ items, className }: PasswordPolicyListProps) {
  return (
    <div className={cn('rounded-2xl border bg-muted/30 p-5', className)}>
      <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Password requirements</p>
      <ul className="space-y-2 text-sm text-foreground/90">
        {items.map((item) => (
          <li key={item} className="flex items-center gap-2.5">
            <div className="h-1.5 w-1.5 shrink-0 rounded-full bg-primary/50" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
