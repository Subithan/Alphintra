import * as React from 'react';
import { cn } from '@/lib/utils';

const buttonVariants = {
  variant: {
    default: 'btn-primary',
    destructive: 'btn-destructive',
    outline: 'btn-outline',
    secondary: 'btn-secondary',
    ghost: 'btn-ghost',
    link: 'btn-link',
  },
  size: {
    default: '',
    sm: 'btn-sm',
    lg: 'btn-lg',
    icon: 'btn-icon',
  },
};

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof buttonVariants.variant;
  size?: keyof typeof buttonVariants.size;
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', asChild = false, ...props }, ref) => {
    const Comp = asChild ? 'span' : 'button';
    
    return (
      <Comp
        className={cn('rounded-lg transition-all', 
          'btn',
          buttonVariants.variant[variant],
          buttonVariants.size[size], 'dark:shadow-none dark:opacity-90',
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);

Button.displayName = 'Button';

export { Button, buttonVariants };