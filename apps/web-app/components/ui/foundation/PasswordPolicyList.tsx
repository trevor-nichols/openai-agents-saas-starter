import { cn } from '@/lib/utils';

interface PasswordPolicyListProps {
  items: readonly string[];
  className?: string;
}

export function PasswordPolicyList({ items, className }: PasswordPolicyListProps) {
  return (
    <div className={cn('rounded-md border border-white/10 bg-white/5 p-3 text-sm', className)}>
      <p className="font-medium text-foreground">Password requirements</p>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-foreground/80">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
