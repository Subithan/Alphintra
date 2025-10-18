'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface BillingInterval {
  value: 'month' | 'year';
  label: string;
  discount?: string;
}

interface PricingToggleProps {
  interval: 'month' | 'year';
  onIntervalChange: (interval: 'month' | 'year') => void;
  className?: string;
}

export function PricingToggle({ interval, onIntervalChange, className }: PricingToggleProps) {
  const intervals: BillingInterval[] = [
    { value: 'month', label: 'Monthly' },
    { value: 'year', label: 'Yearly', discount: 'Save 20%' },
  ];

  return (
    <div className={cn('flex flex-col items-center gap-4', className)}>
      <div className="inline-flex items-center gap-2 rounded-lg bg-muted p-1">
        {intervals.map((item) => (
          <Button
            key={item.value}
            variant={interval === item.value ? 'default' : 'ghost'}
            size="sm"
            onClick={() => onIntervalChange(item.value)}
            className={cn(
              'relative transition-all',
              interval === item.value && 'shadow-sm'
            )}
          >
            {item.label}
            {item.discount && interval !== item.value && (
              <span className="ml-2 text-xs text-green-500">
                {item.discount}
              </span>
            )}
          </Button>
        ))}
      </div>
    </div>
  );
}
