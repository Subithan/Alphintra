// src/frontend/components/subscription/SubscriptionStatus.tsx
'use client';

import React, { useEffect, useState } from 'react';
import { subscriptionApiClient, type SubscriptionDto } from '@/lib/api';

export const SubscriptionStatus: React.FC = () => {
  const [subscription, setSubscription] = useState<SubscriptionDto | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSubscription();
  }, []);

  const loadSubscription = async () => {
    try {
      setLoading(true);
      const data = await subscriptionApiClient.getCurrentSubscription();
      setSubscription(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load subscription');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
      </div>
    );
  }

  if (error || !subscription || !subscription.status) {
    return (
      <div className="text-sm text-gray-500">
        No active subscription
      </div>
    );
  }

  const isActive = subscription.status === 'active';
  const statusColor = isActive ? 'text-green-600' : 'text-yellow-600';
  const bgColor = isActive ? 'bg-green-50' : 'bg-yellow-50';

  return (
    <div className={`${bgColor} rounded-lg p-4`}>
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-medium text-gray-900">
            {subscription.planName?.toUpperCase()} Plan
          </h3>
          <p className={`text-xs ${statusColor} capitalize mt-1`}>
            {subscription.status}
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm font-semibold text-gray-900">
            {subscription.currency?.toUpperCase()} {subscription.amount}
          </p>
          <p className="text-xs text-gray-500">
            per {subscription.interval}
          </p>
        </div>
      </div>
      {subscription.currentPeriodEnd && (
        <p className="text-xs text-gray-500 mt-2">
          {subscription.cancelAtPeriodEnd
            ? `Cancels on: ${new Date(subscription.currentPeriodEnd).toLocaleDateString()}`
            : `Renews on: ${new Date(subscription.currentPeriodEnd).toLocaleDateString()}`}
        </p>
      )}
    </div>
  );
};
