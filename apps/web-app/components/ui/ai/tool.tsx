'use client';

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { cn } from '@/lib/utils';
import type { ToolUIPart } from 'ai';
import {
  CheckIcon,
  ChevronRightIcon,
  GlobeIcon,
  Loader2Icon,
  TriangleAlertIcon,
} from 'lucide-react';
import { type ComponentProps, type ReactNode, isValidElement } from 'react';
import { CodeBlock } from './code-block';

export type ToolProps = ComponentProps<typeof Collapsible>;

export const Tool = ({ className, ...props }: ToolProps) => (
  <Collapsible
    className={cn(
      'group w-fit min-w-[300px] overflow-hidden rounded-xl border border-border/50 bg-background/50',
      className
    )}
    {...props}
  />
);

export type ToolHeaderProps = {
  type: ToolUIPart['type'];
  state: ToolUIPart['state'];
  className?: string;
};

const getStatusIndicator = (status: ToolUIPart['state']) => {
  switch (status) {
    case 'input-streaming':
    case 'input-available':
      return (
        <div className="flex items-center gap-1.5 text-muted-foreground/80">
          <Loader2Icon className="size-3 animate-spin" />
          <span className="text-xs font-medium">Running...</span>
        </div>
      );
    case 'output-available':
      return (
        <div className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-500">
          <CheckIcon className="size-3.5" />
          <span className="text-xs font-medium">Completed</span>
        </div>
      );
    case 'output-error':
      return (
        <div className="flex items-center gap-1.5 text-destructive">
          <TriangleAlertIcon className="size-3.5" />
          <span className="text-xs font-medium">Failed</span>
        </div>
      );
    default:
      return null;
  }
};

export const ToolHeader = ({
  className,
  type,
  state,
  ...props
}: ToolHeaderProps) => (
  <CollapsibleTrigger
    className={cn(
      'flex w-full items-center justify-between gap-6 px-3 py-2 transition-colors hover:bg-muted/50',
      className
    )}
    {...props}
  >
    <div className="flex items-center gap-3">
      <div className="flex size-6 items-center justify-center rounded-md border bg-background shadow-sm">
        <GlobeIcon className="size-3.5 text-muted-foreground" />
      </div>
      <span className="font-medium text-sm text-foreground/90">{type}</span>
    </div>
    <div className="flex items-center gap-3">
      {getStatusIndicator(state)}
      <ChevronRightIcon className="size-4 text-muted-foreground/50 transition-transform duration-200 group-data-[state=open]:rotate-90" />
    </div>
  </CollapsibleTrigger>
);

export type ToolContentProps = ComponentProps<typeof CollapsibleContent>;

export const ToolContent = ({ className, ...props }: ToolContentProps) => (
  <CollapsibleContent
    className={cn(
      'overflow-hidden data-[state=closed]:animate-collapsible-up data-[state=open]:animate-collapsible-down',
      className
    )}
    {...props}
  />
);

export type ToolInputProps = ComponentProps<'div'> & {
  input: ToolUIPart['input'];
};

export const ToolInput = ({ className, input, ...props }: ToolInputProps) => (
  <div
    className={cn('border-t bg-muted/20 px-3 py-2', className)}
    {...props}
  >
    <div className="mb-2 flex items-center gap-2">
      <span className="font-semibold text-[9px] text-muted-foreground uppercase tracking-wider">
        Input
      </span>
    </div>
    <div className="overflow-hidden rounded-lg border bg-background shadow-sm">
      <CodeBlock
        code={JSON.stringify(input, null, 2)}
        language="json"
        className="border-none"
      />
    </div>
  </div>
);

export type ToolOutputProps = ComponentProps<'div'> & {
  output: ReactNode;
  errorText: ToolUIPart['errorText'];
};

export const ToolOutput = ({
  className,
  output,
  errorText,
  ...props
}: ToolOutputProps) => {
  if (!(output || errorText)) {
    return null;
  }

  const isError = !!errorText;

  return (
    <div
      className={cn(
        'border-t bg-muted/20 px-3 py-2',
        isError && 'bg-destructive/5',
        className
      )}
      {...props}
    >
      <div className="mb-2 flex items-center gap-2">
        <span
          className={cn(
            'font-semibold text-[9px] uppercase tracking-wider',
            isError ? 'text-destructive' : 'text-muted-foreground'
          )}
        >
          {isError ? 'Error' : 'Result'}
        </span>
      </div>
      <div
        className={cn(
          'overflow-x-auto rounded-lg border bg-background p-3 text-xs font-mono shadow-sm',
          isError && 'border-destructive/20 text-destructive'
        )}
      >
        {isError ? (
          <div className="whitespace-pre-wrap">{errorText}</div>
        ) : (
          <div className="whitespace-pre-wrap text-muted-foreground">
            {isValidElement(output) || typeof output === 'string'
              ? output
              : JSON.stringify(output, null, 2)}
          </div>
        )}
      </div>
    </div>
  );
};