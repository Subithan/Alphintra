'use client';

import React, { useEffect, useState } from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { 
  SubscriptionCard, 
  SubscriptionComparison, 
  SubscriptionHeader, 
  SubscriptionFAQ 
} from '@/components/subscriptions';
import type { SubscriptionPlan } from '@/components/subscriptions';
import { Card, CardContent } from '@/components/ui/no-code/card';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { useRouter } from 'next/navigation';

interface SubscriptionModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SubscriptionModal({ isOpen, onClose }: SubscriptionModalProps) {
  const { toast } = useToast();
  const router = useRouter();
  const [showComparison, setShowComparison] = useState(false);
  const [isLoading, setIsLoading] = useState<string | null>(null);
  const [currentPlan] = useState<string | undefined>(undefined);

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  // Define subscription plans
  const plans: SubscriptionPlan[] = [
    {
      id: 'pro',
      name: 'Pro',
      price: 20,
      currency: 'USD',
      interval: 'month',
      description: 'Perfect for individual traders and small teams',
      badge: 'Best Value',
      popular: true,
      features: [
        { text: 'Up to 1 active trading strategy', included: true },
        { text: 'Real-time market data', included: true },
        { text: 'Advanced technical indicators', included: true },
        { text: 'Automated strategy execution', included: true },
        { text: 'Backtesting with 2 years of historical data', included: true },
        { text: 'Mobile app access', included: true },
        { text: 'Portfolio analytics', included: true },
        { text: 'Single exchange support', included: true },
        { text: 'Custom webhooks', included: false },
        { text: 'Priority support', included: false },
        { text: 'Advanced AI insights', included: false },
      ],
    },
    {
      id: 'max',
      name: 'Max',
      price: 200,
      currency: 'USD',
      interval: 'month',
      description: 'Ultimate power for professional traders and institutions',
      badge: 'Premium',
      comingSoon: true,
      features: [
        { text: 'Unlimited active trading strategies', included: true },
        { text: 'Unlimited API calls', included: true },
        { text: 'Real-time market data', included: true },
        { text: 'Advanced technical indicators', included: true },
        { text: 'Automated strategy execution', included: true },
        { text: 'Backtesting with 10 years of historical data', included: true },
        { text: 'Priority support (1h response)', included: true },
        { text: 'Mobile app access', included: true },
        { text: 'Advanced risk management & hedging', included: true },
        { text: 'Portfolio analytics & reporting', included: true },
        { text: 'Multi-exchange support (unlimited)', included: true },
        { text: 'Custom webhooks & integrations', included: true },
        { text: 'Dedicated account manager', included: true },
        { text: 'Advanced AI insights & predictions', included: true },
        { text: 'White-label options', included: true },
        { text: 'Custom indicator development', included: true },
      ],
    },
  ];

  // Comparison features
  const comparisonFeatures = [
    {
      name: 'Active Strategies',
      pro: '1 strategy',
      max: 'Unlimited',
      description: 'Number of strategies you can run simultaneously',
    },
    {
      name: 'Historical Data',
      pro: '2 years',
      max: '10 years',
      description: 'Access to historical market data for backtesting',
    },
    {
      name: 'Exchange Support',
      pro: '1 exchange',
      max: 'Unlimited',
      description: 'Number of exchanges you can connect',
    },
    {
      name: 'Real-time Market Data',
      pro: true,
      max: true,
    },
    {
      name: 'Technical Indicators',
      pro: true,
      max: true,
    },
    {
      name: 'Automated Execution',
      pro: true,
      max: true,
    },
    {
      name: 'Mobile App',
      pro: true,
      max: true,
    },
    {
      name: 'Custom Webhooks',
      pro: false,
      max: true,
    },
    {
      name: 'Priority Support',
      pro: false,
      max: true,
      description: '1-hour response time for urgent issues',
    },
    {
      name: 'AI Insights',
      pro: false,
      max: true,
      description: 'Advanced AI-powered trading insights',
    },
    {
      name: 'Dedicated Manager',
      pro: false,
      max: true,
    },
    {
      name: 'White-label Options',
      pro: false,
      max: true,
    },
  ];

  const handleSubscribe = async (planId: string) => {
    setIsLoading(planId);

    try {
      // Show loading toast
      toast({
        title: 'Redirecting to Payment',
        description: `Opening payment page for ${planId.toUpperCase()} plan...`,
      });

      // Close modal
      onClose();

      // Navigate to payment page with plan information
      router.push(`/subscription/payment?plan=${planId}`);
    } catch (error) {
      toast({
        title: 'Navigation Failed',
        description: 'Unable to open payment page. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto">
      {/* Backdrop with blur */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal Content */}
      <div className="relative w-full max-w-7xl mx-auto p-4 md:p-6 my-8">
        <div className="relative bg-background rounded-2xl shadow-2xl border border-border">
          {/* Close Button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 z-10 p-2 rounded-full bg-background/80 backdrop-blur-sm border border-border hover:bg-muted transition-colors text-black dark:text-white"
            aria-label="Close modal"
          >
            <X className="h-5 w-5" />
          </button>

          {/* Scrollable Content */}
          <div className="overflow-y-auto max-h-[85vh] p-6 md:p-8 lg:p-12">
            <div className="space-y-12">
              {/* Header */}
              <SubscriptionHeader />

              {/* Subscription Plans */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-12 max-w-6xl mx-auto">
                {plans.map((plan) => (
                  <SubscriptionCard
                    key={plan.id}
                    plan={plan}
                    onSubscribe={handleSubscribe}
                    isLoading={isLoading === plan.id}
                    currentPlan={currentPlan}
                  />
                ))}
              </div>

              {/* Toggle Comparison Button */}
              <div className="text-center">
                <Button
                  variant="outline"
                  size="lg"
                  onClick={() => setShowComparison(!showComparison)}
                  className="gap-2 text-black dark:text-white border-black dark:border-white hover:bg-black/10 dark:hover:bg-white/10"
                >
                  {showComparison ? (
                    <>
                      Hide Detailed Comparison
                      <ChevronUp className="h-4 w-4" />
                    </>
                  ) : (
                    <>
                      Show Detailed Comparison
                      <ChevronDown className="h-4 w-4" />
                    </>
                  )}
                </Button>
              </div>

              {/* Detailed Comparison Table */}
              {showComparison && (
                <Card className="max-w-6xl mx-auto overflow-hidden">
                  <CardContent className="p-6">
                    <h2 className="text-2xl font-bold text-center mb-6">
                      Detailed Plan Comparison
                    </h2>
                    <SubscriptionComparison features={comparisonFeatures} />
                  </CardContent>
                </Card>
              )}

              {/* FAQ Section */}
              <div className="max-w-6xl mx-auto">
                <SubscriptionFAQ />
              </div>

              {/* Trust Indicators */}
              <div className="max-w-4xl mx-auto">
                <Card className="bg-gradient-to-r from-primary/5 via-purple-500/5 to-pink-500/5 border-primary/20">
                  <CardContent className="p-8 text-center space-y-4">
                    <h3 className="text-2xl font-bold">
                      Trusted by Thousands of Traders Worldwide
                    </h3>
                    <p className="text-muted-foreground max-w-2xl mx-auto">
                      Join our community of successful traders using our trading engine to automate
                      their strategies and maximize their profits.
                    </p>
                    <div className="flex flex-wrap justify-center gap-8 pt-6">
                      <div className="text-center">
                        <div className="text-3xl font-bold text-primary">99.9%</div>
                        <div className="text-sm text-muted-foreground">Uptime</div>
                      </div>
                      <div className="text-center">
                        <div className="text-3xl font-bold text-primary">&lt;50ms</div>
                        <div className="text-sm text-muted-foreground">Latency</div>
                      </div>
                      <div className="text-center">
                        <div className="text-3xl font-bold text-primary">10K+</div>
                        <div className="text-sm text-muted-foreground">Active Users</div>
                      </div>
                      <div className="text-center">
                        <div className="text-3xl font-bold text-primary">$2B+</div>
                        <div className="text-sm text-muted-foreground">Trading Volume</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
