import { forwardRef, HTMLAttributes } from 'react';
import { Card } from '@/components/ui/no-code/card';
import { cn } from '@/lib/utils';

export const GlassPanel = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('glass-panel', className)} {...props} />
  )
);
GlassPanel.displayName = 'GlassPanel';

export const GlassCard = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <Card ref={ref} className={cn('glass-card', className)} {...props} />
  )
);
GlassCard.displayName = 'GlassCard';
