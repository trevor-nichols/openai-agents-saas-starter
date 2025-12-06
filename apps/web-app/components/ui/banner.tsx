'use client';

import { useControllableState } from '@radix-ui/react-use-controllable-state';
import { type LucideIcon, XIcon } from 'lucide-react';
import {
  type ComponentProps,
  createContext,
  type HTMLAttributes,
  type MouseEventHandler,
  useContext,
} from 'react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

type BannerContextProps = {
  show: boolean;
  setShow: (show: boolean) => void;
};

export const BannerContext = createContext<BannerContextProps>({
  show: true,
  setShow: () => {},
});

export type BannerProps = HTMLAttributes<HTMLDivElement> & {
  visible?: boolean;
  defaultVisible?: boolean;
  onClose?: () => void;
  inset?: boolean;
  variant?: 'primary' | 'muted';
};

export const Banner = ({
  children,
  visible,
  defaultVisible = true,
  onClose,
  className,
  inset = false,
  variant = 'primary',
  ...props
}: BannerProps) => {
  const [show, setShow] = useControllableState({
    defaultProp: defaultVisible,
    prop: visible,
    onChange: onClose,
  });

  if (!show) {
    return null;
  }

  return (
    <BannerContext.Provider value={{ show, setShow }}>
      <div
        className={cn(
          'flex w-full items-center justify-between gap-3 px-4 py-3 transition-all animate-in fade-in slide-in-from-top-2 duration-300',
          variant === 'primary'
            ? 'bg-primary text-primary-foreground shadow-md shadow-primary/20'
            : 'bg-muted/50 border-transparent text-foreground shadow-sm',
          inset && 'rounded-3xl',
          className
        )}
        {...props}
      >
        {children}
      </div>
    </BannerContext.Provider>
  );
};

export type BannerIconProps = HTMLAttributes<HTMLDivElement> & {
  icon: LucideIcon;
};

export const BannerIcon = ({
  icon: Icon,
  className,
  ...props
}: BannerIconProps) => (
  <div
    className={cn(
      'flex shrink-0 items-center justify-center rounded-full bg-background/20 p-1.5',
      className
    )}
    {...props}
  >
    <Icon size={16} />
  </div>
);

export type BannerTitleProps = HTMLAttributes<HTMLParagraphElement>;

export const BannerTitle = ({ className, ...props }: BannerTitleProps) => (
  <p className={cn('flex-1 text-sm font-medium tracking-tight', className)} {...props} />
);

export type BannerActionProps = ComponentProps<typeof Button>;

export const BannerAction = ({
  variant = 'outline',
  size = 'sm',
  className,
  ...props
}: BannerActionProps) => (
  <Button
    className={cn(
      'h-8 shrink-0 rounded-full border-background/20 px-4 text-xs font-semibold hover:bg-background/10 hover:text-current hover:border-background/40',
      className
    )}
    size={size}
    variant={variant}
    {...props}
  />
);

export type BannerCloseProps = ComponentProps<typeof Button>;

export const BannerClose = ({
  variant = 'ghost',
  size = 'icon',
  onClick,
  className,
  ...props
}: BannerCloseProps) => {
  const { setShow } = useContext(BannerContext);

  const handleClick: MouseEventHandler<HTMLButtonElement> = (e) => {
    setShow(false);
    onClick?.(e);
  };

  return (
    <Button
      className={cn(
        'h-7 w-7 shrink-0 rounded-full hover:bg-background/20 hover:text-current',
        className
      )}
      onClick={handleClick}
      size={size}
      variant={variant}
      {...props}
    >
      <XIcon size={14} />
    </Button>
  );
};
