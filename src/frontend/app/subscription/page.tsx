// src/frontend/app/subscription/page.tsx
'use client';

import React, { useEffect, useState } from 'react';
import { SubscriptionPlans } from '@/components/subscription/SubscriptionPlans';
import { SubscriptionStatus } from '@/components/subscription/SubscriptionStatus';
import { subscriptionApiClient } from '@/lib/api';

export default function SubscriptionPage() {
  const [currentPlan, setCurrentPlan] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCurrentSubscription();
  }, []);

  const loadCurrentSubscription = async () => {
    try {
      const status = await subscriptionApiClient.getSubscriptionStatus();
      if (status.hasSubscription && status.subscription) {
        setCurrentPlan(status.subscription.planName);
      }
    } catch (error) {
      console.error('Failed to load subscription:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="px-4 py-6 sm:px-0">
          <h1 className="text-3xl font-bold text-gray-900">Subscription Management</h1>
          <p className="mt-2 text-sm text-gray-600">
            Manage your subscription and billing information
          </p>
        </div>

        {/* Current Subscription Status */}
        {!loading && (
          <div className="px-4 py-4 sm:px-0 mb-8">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Current Subscription</h2>
            <SubscriptionStatus />
          </div>
        )}

        {/* Subscription Plans */}
        <SubscriptionPlans currentPlan={currentPlan} />
      </div>
    </div>
  );
}
