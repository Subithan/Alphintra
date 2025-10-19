// src/frontend/components/subscription/SubscriptionPlans.tsx
'use client';

import React, { useState } from 'react';
import { subscriptionApiClient, SUBSCRIPTION_PLANS } from '@/lib/api';

interface SubscriptionPlansProps {
  currentPlan?: string;
}

export const SubscriptionPlans: React.FC<SubscriptionPlansProps> = ({ currentPlan }) => {
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubscribe = async (planName: 'BASIC' | 'PRO' | 'ENTERPRISE') => {
    try {
      setLoading(planName);
      setError(null);
      await subscriptionApiClient.redirectToCheckout(planName);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start subscription');
      setLoading(null);
    }
  };

  return (
    <div className="py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
            Choose Your Trading Plan
          </h2>
          <p className="mt-4 text-xl text-gray-600">
            Select the perfect plan for your algorithmic trading needs
          </p>
        </div>

        {error && (
          <div className="mt-4 bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <div className="mt-12 space-y-4 sm:mt-16 sm:space-y-0 sm:grid sm:grid-cols-3 sm:gap-6 lg:max-w-4xl lg:mx-auto xl:max-w-none xl:mx-0">
          {Object.entries(SUBSCRIPTION_PLANS).map(([key, plan]) => {
            const planKey = key as 'BASIC' | 'PRO' | 'ENTERPRISE';
            const isCurrentPlan = currentPlan?.toUpperCase() === planKey;
            const isLoading = loading === planKey;

            return (
              <div
                key={key}
                className={`border rounded-lg shadow-sm divide-y divide-gray-200 ${
                  planKey === 'PRO' ? 'border-indigo-500 border-2' : 'border-gray-200'
                }`}
              >
                <div className="p-6">
                  {planKey === 'PRO' && (
                    <span className="inline-flex px-4 py-1 rounded-full text-sm font-semibold tracking-wide uppercase bg-indigo-100 text-indigo-600">
                      Most Popular
                    </span>
                  )}
                  <h3 className="text-lg leading-6 font-medium text-gray-900 mt-2">
                    {plan.name}
                  </h3>
                  <p className="mt-4">
                    <span className="text-4xl font-extrabold text-gray-900">{plan.price}</span>
                    <span className="text-base font-medium text-gray-500">/{plan.interval}</span>
                  </p>
                  <button
                    onClick={() => handleSubscribe(planKey)}
                    disabled={isCurrentPlan || isLoading}
                    className={`mt-8 block w-full py-3 px-6 border border-transparent rounded-md text-center font-medium ${
                      isCurrentPlan
                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        : planKey === 'PRO'
                        ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                        : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100'
                    }`}
                  >
                    {isLoading
                      ? 'Processing...'
                      : isCurrentPlan
                      ? 'Current Plan'
                      : 'Subscribe'}
                  </button>
                </div>
                <div className="pt-6 pb-8 px-6">
                  <h4 className="text-sm font-medium text-gray-900 tracking-wide uppercase">
                    What's included
                  </h4>
                  <ul className="mt-6 space-y-4">
                    {plan.features.map((feature, index) => (
                      <li key={index} className="flex space-x-3">
                        <svg
                          className="flex-shrink-0 h-5 w-5 text-green-500"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                        <span className="text-sm text-gray-500">{feature}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
