'use client';

import React from 'react';
import { Zap, TrendingUp, Shield, Clock } from 'lucide-react';

export function SubscriptionHeader() {
  const benefits = [
    {
      icon: <Zap className="h-5 w-5" />,
      text: "Lightning-fast execution"
    },
    {
      icon: <TrendingUp className="h-5 w-5" />,
      text: "Advanced trading strategies"
    },
    {
      icon: <Shield className="h-5 w-5" />,
      text: "Enterprise-grade security"
    },
    {
      icon: <Clock className="h-5 w-5" />,
      text: "24/7 trading support"
    }
  ];

  return (
    <div className="text-center space-y-6 mb-12">
      <div className="space-y-3">
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight bg-gradient-to-r from-primary via-purple-500 to-pink-500 bg-clip-text text-transparent">
          Choose Your Trading Plan
        </h1>
        <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
          Unlock the power of automated trading with our professional-grade trading engine.
          Select the perfect plan for your trading needs.
        </p>
      </div>

      <div className="flex flex-wrap justify-center gap-6 pt-4">
        {benefits.map((benefit, index) => (
          <div 
            key={index}
            className="flex items-center gap-2 text-sm text-muted-foreground"
          >
            <div className="text-primary">
              {benefit.icon}
            </div>
            <span>{benefit.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
