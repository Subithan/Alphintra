'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/no-code/card';
import { Badge } from '@/components/ui/no-code/badge';
import { Button } from '@/components/ui/button';
import { Check, Zap, Crown, Lock } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface SubscriptionFeature {
  text: string;
  included: boolean;
}

export interface SubscriptionPlan {
  id: string;
  name: string;
  price: number;
  currency: string;
  interval: 'month' | 'year';
  description: string;
  features: SubscriptionFeature[];
  popular?: boolean;
  comingSoon?: boolean;
  badge?: string;
  icon?: React.ReactNode;
}

interface SubscriptionCardProps {
  plan: SubscriptionPlan;
  onSubscribe?: (planId: string) => void;
  isLoading?: boolean;
  currentPlan?: string;
}

export function SubscriptionCard({ 
  plan, 
  onSubscribe, 
  isLoading = false,
  currentPlan 
}: SubscriptionCardProps) {
  const isCurrentPlan = currentPlan === plan.id;
  const isDisabled = plan.comingSoon || isLoading || isCurrentPlan;

  const getIcon = () => {
    if (plan.icon) return plan.icon;
    if (plan.name === 'Pro') return <Zap className="h-6 w-6" />;
    if (plan.name === 'Max') return <Crown className="h-6 w-6" />;
    return <Zap className="h-6 w-6" />;
  };

  return (
    <Card 
      className={cn(
        "relative flex flex-col h-full transition-all duration-300",
        plan.popular && "border-primary shadow-xl scale-105",
        plan.comingSoon && "opacity-75",
        isCurrentPlan && "border-green-500"
      )}
    >
      {/* Popular Badge */}
      {plan.popular && !plan.comingSoon && (
        <div className="absolute -top-4 left-1/2 -translate-x-1/2">
          <Badge className="bg-gradient-to-r from-primary to-purple-600 text-white px-4 py-1">
            Most Popular
          </Badge>
        </div>
      )}

      {/* Coming Soon Badge */}
      {plan.comingSoon && (
        <div className="absolute -top-4 left-1/2 -translate-x-1/2">
          <Badge className="bg-gradient-to-r from-orange-500 to-red-500 text-white px-4 py-1">
            Coming Soon
          </Badge>
        </div>
      )}

      {/* Current Plan Badge */}
      {isCurrentPlan && (
        <div className="absolute -top-4 right-4">
          <Badge className="bg-green-500 text-white px-4 py-1">
            Current Plan
          </Badge>
        </div>
      )}

      <CardHeader className="text-center pb-8 pt-10">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
          {plan.comingSoon ? (
            <Lock className="h-8 w-8 text-muted-foreground" />
          ) : (
            <div className={cn(
              "text-primary",
              plan.popular && "animate-pulse"
            )}>
              {getIcon()}
            </div>
          )}
        </div>
        
        <CardTitle className="text-3xl font-bold">
          {plan.name}
        </CardTitle>
        
        {plan.badge && (
          <Badge variant="secondary" className="mt-2 mx-auto">
            {plan.badge}
          </Badge>
        )}
        
        <CardDescription className="mt-3 text-base">
          {plan.description}
        </CardDescription>
        
        <div className="mt-6">
          <div className="flex items-baseline justify-center gap-x-2">
            <span className="text-5xl font-bold tracking-tight">
              ${plan.price}
            </span>
            <span className="text-sm font-semibold leading-6 tracking-wide text-muted-foreground">
              /{plan.interval}
            </span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 px-6">
        <ul className="space-y-4">
          {plan.features.map((feature, index) => (
            <li key={index} className="flex items-start gap-x-3">
              <Check 
                className={cn(
                  "h-5 w-5 flex-shrink-0 mt-0.5",
                  feature.included 
                    ? "text-green-500" 
                    : "text-muted-foreground opacity-30"
                )} 
              />
              <span 
                className={cn(
                  "text-sm leading-6",
                  feature.included 
                    ? "text-foreground" 
                    : "text-muted-foreground line-through opacity-50"
                )}
              >
                {feature.text}
              </span>
            </li>
          ))}
        </ul>
      </CardContent>

      <CardFooter className="px-6 pb-8">
        <Button
          onClick={() => onSubscribe?.(plan.id)}
          disabled={isDisabled}
          className={cn(
            "w-full text-base font-semibold py-6",
            plan.popular && !plan.comingSoon && "bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-700",
            isCurrentPlan && "bg-green-500 hover:bg-green-600",
            plan.comingSoon && "cursor-not-allowed"
          )}
          variant={plan.popular && !isCurrentPlan ? "default" : "outline"}
        >
          {isLoading ? (
            <span className="flex items-center gap-2">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
              Processing...
            </span>
          ) : isCurrentPlan ? (
            "Current Plan"
          ) : plan.comingSoon ? (
            <span className="flex items-center gap-2">
              <Lock className="h-4 w-4" />
              Coming Soon
            </span>
          ) : (
            "Subscribe Now"
          )}
        </Button>
      </CardFooter>
    </Card>
  );
}
