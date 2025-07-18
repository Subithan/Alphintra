'use client';

import React, { useState } from 'react';
import {
  ListTodo,
  Clock,
  Wallet,
  TrendingUp
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

export interface StepData {
  id: string;
  title: string;
  icon: React.ComponentType<any>;
  status: 'pending' | 'active' | 'completed' | 'failed';
  content: React.ReactNode;
}

interface FormStepperProps {
  className?: string;
}

export function VerifyStepper({ className }: FormStepperProps) {
  const [activeStep, setActiveStep] = useState(0);
  const [isVerified, setIsVerified] = useState(false);
  const [isDeposited, setIsDeposited] = useState(false);

  const steps: StepData[] = [
    {
      id: 'verify',
      title: 'Verify',
      icon: ListTodo,
      status: isVerified ? 'completed' : 'active',
      content: (
        <div className="space-y-4">
          <div className="flex items-center justify-center mb-6">
            <div className="w-24 h-24 bg-yellow-500/10 rounded-full flex items-center justify-center">
              <ListTodo className="w-12 h-12 text-yellow-500" />
            </div>
          </div>
          <div className="text-center space-y-2">
            <h3 className="text-lg font-semibold text-black dark:text-white">
              {isVerified ? 'Verified' : 'Verify'}
            </h3>
            <p className="text-muted-foreground text-sm">
              {isVerified
                ? 'Verification complete. View your verification details.'
                : 'Verify to continue deposit and trade.'}
            </p>
          </div>
          <Button className="w-full bg-yellow-500 hover:bg-yellow-500 hover:scale-105 transition-transform">
            {isVerified ? 'View Details' : 'Verify'}
          </Button>
        </div>
      ),
    },
    {
        id: 'deposit',
        title: 'Deposit',
        icon: Wallet,
        status: isVerified
            ? isDeposited
            ? 'completed'
            : 'active'
            : 'pending',
        content: (
            <div className="space-y-4">
            <div className="flex items-center justify-center mb-6">
                <div className="w-24 h-24 bg-yellow-500/10 rounded-full flex items-center justify-center">
                <Wallet className="w-12 h-12 text-yellow-500" />
                </div>
            </div>
            <div className="text-center space-y-2">
                <h3 className="text-lg font-semibold  text-black dark:text-white">
                {isDeposited ? 'Deposited' : 'Deposit Funds'}
                </h3>
                <p className="text-muted-foreground text-sm">
                {isDeposited
                    ? 'Funds added successfully. You can now trade.'
                    : 'Add funds to your account to start trading.'}
                </p>
            </div>
            {isVerified ? (
                <Button
                className="w-full bg-yellow-500 hover:bg-yellow-600 hover:scale-105 transition-transform"
                onClick={() => setIsDeposited(true)}
                >
                {isDeposited ? 'View Receipt' : 'Deposit'}
                </Button>
            ) : (
                <div className="flex items-center justify-center gap-2 text-muted-foreground">
                <Clock className="w-4 h-4" />
                <span className="text-sm">Pending</span>
                </div>
            )}
            </div>
        ),
    },
    {
        id: 'trade',
        title: 'Trade',
        icon: TrendingUp,
        status: isDeposited ? 'active' : 'pending',
        content: (
            <div className="space-y-4">
            <div className="flex items-center justify-center mb-6">
                <div className="w-24 h-24 bg-yellow-500/10 rounded-full flex items-center justify-center">
                <TrendingUp className="w-12 h-12 text-yellow-500" />
                </div>
            </div>
            <div className="text-center space-y-2">
                <h3 className="text-lg font-semibold  text-black dark:text-white">Trade</h3>
                <p className="text-muted-foreground text-sm">
                Start trading once verification and deposit are complete.
                </p>
            </div>
            {isDeposited ? (
                <Button className="w-full bg-yellow-500 hover:bg-yellow-600 hover:scale-105 transition-transform">
                Start Trading
                </Button>
            ) : (
                <div className="flex items-center justify-center gap-2 text-muted-foreground">
                <Clock className="w-4 h-4" />
                <span className="text-sm">Pending</span>
                </div>
            )}
            </div>
        ),
    },

  ];

  const getStepIcon = (step: StepData, index: number) => (
    <div
      className={cn(
        'w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold border-2 transition-colors',
        index === activeStep
        ? 'bg-yellow-500 text-primary-foreground border-yellow-500'
        : step.status === 'completed'
        ? 'bg-green-500 text-white border-green-500'
        : step.status === 'failed'
        ? 'bg-destructive text-destructive-foreground border-destructive'
        : 'bg-muted text-muted-foreground border-stepper-inactive'
      )}
    >
      {index + 1}
    </div>
  );

  const getConnectorLine = (index: number) => {
    if (index === steps.length - 1) return null;
    return <div className="hidden md:block flex-1 h-0.5 bg-stepper-line mx-4 bg-[#222c3e]" />;
  };

  return (
    <div className={cn('w-full max-w-6xl mx-auto p-6', className)}>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">Get Started</h1>
      </div>

      {/* Desktop Horizontal Stepper */}
      <div className="hidden md:block">
        <div className="flex items-center justify-between mb-8">
          {steps.map((step, index) => (
            <React.Fragment key={step.id}>
              <button
                onClick={() => setActiveStep(index)}
                className="flex flex-col items-center gap-2 min-w-0 transition-opacity hover:opacity-80 "
              >
                {getStepIcon(step, index)}
              </button>
              {getConnectorLine(index)}
            </React.Fragment>
          ))}
        </div>

        <div className="grid grid-cols-3 gap-6">
          {steps.map((step, index) => (
            <div
              key={step.id}
              className={cn(
                'p-6 transition-all duration-300 cursor-pointer rounded-3xl',
                index === activeStep
                  ? 'scale-105 bg-card border border-yellow-500 '
                  : 'scale-95 opacity-60 bg-card/50 border border-[#222c3e]'
              )}
              onClick={() => setActiveStep(index)}
            >
              <div
                className={cn(
                  'transition-all duration-300',
                  index === activeStep ? 'opacity-100' : 'opacity-60'
                )}
              >
                {step.content}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Mobile Vertical Stepper */}
      <div className="md:hidden space-y-4">
        {steps.map((step, index) => (
          <div
            key={step.id}
            className={cn(
              'transition-all duration-300 cursor-pointer rounded-2xl',
              index === activeStep ? 'border border-yellow-500' : 'border  border-[#222c3e]'
            )}
            onClick={() => setActiveStep(index)}
          >
            <div className="p-4">
              <div className="flex items-center gap-3 mb-3">
                {getStepIcon(step, index)}
              </div>
              <div
                className={cn(
                  'transition-all duration-300',
                  index === activeStep
                    ? 'opacity-100 max-h-96 overflow-visible'
                    : 'opacity-60 max-h-0 overflow-hidden'
                )}
              >
                {index === activeStep && <div className="pt-2">{step.content}</div>}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
