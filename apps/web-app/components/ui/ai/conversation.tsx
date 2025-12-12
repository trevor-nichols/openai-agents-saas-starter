'use client';

import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import { ArrowDownIcon } from 'lucide-react';
import type { ComponentProps, ReactNode } from 'react';
import { createContext, useCallback, useContext, useMemo } from 'react';
import { useStickToBottom, type StickToBottomInstance, type StickToBottomOptions } from 'use-stick-to-bottom';

type ConversationContextValue = Pick<
  StickToBottomInstance,
  'contentRef' | 'scrollToBottom' | 'isAtBottom'
>;

const ConversationContext = createContext<ConversationContextValue | null>(null);

function useConversationContext() {
  const context = useContext(ConversationContext);
  if (!context) {
    throw new Error('Conversation components must be used within <Conversation>.');
  }
  return context;
}

export type ConversationProps = StickToBottomOptions & {
  className?: string;
  children: ReactNode;
};

export const Conversation = ({
  className,
  children,
  initial = 'smooth',
  resize = 'smooth',
  targetScrollTop,
  mass,
  damping,
  stiffness,
}: ConversationProps) => {
  const instance = useStickToBottom({
    initial,
    resize,
    targetScrollTop,
    mass,
    damping,
    stiffness,
  });

  const contextValue = useMemo<ConversationContextValue>(
    () => ({
      contentRef: instance.contentRef,
      scrollToBottom: instance.scrollToBottom,
      isAtBottom: instance.isAtBottom,
    }),
    [instance.contentRef, instance.isAtBottom, instance.scrollToBottom],
  );

  return (
    <ConversationContext.Provider value={contextValue}>
      <ScrollArea
        className={cn('relative flex-1 min-h-0', className)}
        viewportRef={instance.scrollRef}
        viewportClassName="h-full w-full"
        role="log"
      >
        {children}
      </ScrollArea>
    </ConversationContext.Provider>
  );
};

export type ConversationContentProps = ComponentProps<'div'>;

export const ConversationContent = ({
  className,
  ...props
}: ConversationContentProps) => {
  const { contentRef } = useConversationContext();
  return <div ref={contentRef} className={cn('p-4', className)} {...props} />;
};

export type ConversationScrollButtonProps = ComponentProps<typeof Button>;

export const ConversationScrollButton = ({
  className,
  ...props
}: ConversationScrollButtonProps) => {
  const { isAtBottom, scrollToBottom } = useConversationContext();

  const handleScrollToBottom = useCallback(() => {
    scrollToBottom();
  }, [scrollToBottom]);

  return (
    !isAtBottom && (
      <Button
        className={cn(
          'absolute bottom-4 left-[50%] translate-x-[-50%] rounded-full',
          className
        )}
        onClick={handleScrollToBottom}
        size="icon"
        type="button"
        variant="outline"
        {...props}
      >
        <ArrowDownIcon className="size-4" />
      </Button>
    )
  );
};
