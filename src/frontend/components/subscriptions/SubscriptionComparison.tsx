'use client';

import React from 'react';
import { Check, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ComparisonFeature {
  name: string;
  pro: boolean | string;
  max: boolean | string;
  description?: string;
}

interface SubscriptionComparisonProps {
  features: ComparisonFeature[];
}

export function SubscriptionComparison({ features }: SubscriptionComparisonProps) {
  const renderValue = (value: boolean | string) => {
    if (typeof value === 'boolean') {
      return value ? (
        <Check className="h-5 w-5 text-green-500 mx-auto" />
      ) : (
        <X className="h-5 w-5 text-muted-foreground opacity-30 mx-auto" />
      );
    }
    return <span className="text-sm font-medium">{value}</span>;
  };

  return (
    <div className="w-full overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b-2 border-border">
            <th className="text-left py-4 px-4 font-semibold text-base">
              Feature
            </th>
            <th className="text-center py-4 px-4 font-semibold text-base">
              Pro
            </th>
            <th className="text-center py-4 px-4 font-semibold text-base">
              Max
            </th>
          </tr>
        </thead>
        <tbody>
          {features.map((feature, index) => (
            <tr 
              key={index} 
              className={cn(
                "border-b border-border hover:bg-muted/50 transition-colors",
                index % 2 === 0 && "bg-muted/20"
              )}
            >
              <td className="py-4 px-4">
                <div className="flex flex-col">
                  <span className="text-sm font-medium">{feature.name}</span>
                  {feature.description && (
                    <span className="text-xs text-muted-foreground mt-1">
                      {feature.description}
                    </span>
                  )}
                </div>
              </td>
              <td className="py-4 px-4 text-center">
                {renderValue(feature.pro)}
              </td>
              <td className="py-4 px-4 text-center">
                {renderValue(feature.max)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
