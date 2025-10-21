'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/no-code/card';
import { ArrowLeft, CreditCard, Lock, Check, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { SearchParamsWrapper } from '@/components/hooks/use-search-params';

interface PaymentFormData {
  cardNumber: string;
  cardName: string;
  expiryDate: string;
  cvv: string;
  amount: string;
}

interface FormErrors {
  cardNumber?: string;
  cardName?: string;
  expiryDate?: string;
  cvv?: string;
  amount?: string;
}

function PaymentPageContent({ searchParams }: { searchParams: URLSearchParams }) {
  const router = useRouter();
  const planId = searchParams.get('plan');
  const [planDetails, setPlanDetails] = useState<{
    name: string;
    price: number;
    currency: string;
  } | null>(null);

  // Payment form state
  const [formData, setFormData] = useState<PaymentFormData>({
    cardNumber: '',
    cardName: '',
    expiryDate: '',
    cvv: '',
    amount: '20.00'
  });
  
  const [errors, setErrors] = useState<FormErrors>({});
  const [isProcessing, setIsProcessing] = useState(false);
  const [paymentSuccess, setPaymentSuccess] = useState(false);

  useEffect(() => {
    // Map plan IDs to plan details
    const plans = {
      pro: {
        name: 'Pro Plan',
        price: 20,
        currency: 'USD',
      },
      max: {
        name: 'Max Plan',
        price: 200,
        currency: 'USD',
      },
    };

    if (planId && (planId === 'pro' || planId === 'max')) {
      const plan = plans[planId as keyof typeof plans];
      setPlanDetails(plan);
      // Update amount based on plan
      setFormData(prev => ({ ...prev, amount: plan.price.toFixed(2) }));
    } else {
      // If no valid plan, redirect back to subscriptions
      router.push('/subscriptions');
    }
  }, [planId, router]);

  const formatCardNumber = (value: string) => {
    const cleaned = value.replace(/\s/g, '');
    const match = cleaned.match(/.{1,4}/g);
    return match ? match.join(' ') : cleaned;
  };

  const formatExpiryDate = (value: string) => {
    const cleaned = value.replace(/\D/g, '');
    if (cleaned.length >= 2) {
      return cleaned.slice(0, 2) + '/' + cleaned.slice(2, 4);
    }
    return cleaned;
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    let formattedValue = value;

    if (name === 'cardNumber') {
      formattedValue = formatCardNumber(value.replace(/\s/g, '').slice(0, 16));
    } else if (name === 'expiryDate') {
      formattedValue = formatExpiryDate(value.slice(0, 5));
    } else if (name === 'cvv') {
      formattedValue = value.replace(/\D/g, '').slice(0, 4);
    }

    setFormData(prev => ({ ...prev, [name]: formattedValue }));
    if (errors[name as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (formData.cardNumber.replace(/\s/g, '').length !== 16) {
      newErrors.cardNumber = 'Card number must be 16 digits';
    }

    if (formData.cardName.trim().length < 3) {
      newErrors.cardName = 'Please enter a valid name';
    }

    const expiryMatch = formData.expiryDate.match(/^(\d{2})\/(\d{2})$/);
    if (!expiryMatch) {
      newErrors.expiryDate = 'Invalid expiry date';
    } else {
      const month = parseInt(expiryMatch[1]);
      if (month < 1 || month > 12) {
        newErrors.expiryDate = 'Invalid month';
      }
    }

    if (formData.cvv.length < 3) {
      newErrors.cvv = 'CVV must be 3-4 digits';
    }

    if (!formData.amount || parseFloat(formData.amount) <= 0) {
      newErrors.amount = 'Invalid amount';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setIsProcessing(true);

    try {
      // Get userId from localStorage
      const userIdStr = localStorage.getItem('userId') || sessionStorage.getItem('userId');
      
      if (!userIdStr) {
        throw new Error('User ID not found. Please log in again.');
      }

      const userId = parseInt(userIdStr);

      // Call simple backend endpoint to activate subscription
      const response = await fetch('https://api.alphintra.com/api/auth/activate-subscription', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          userId: userId,
          planName: planId // Send the plan name (pro or max)
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Payment confirmation failed');
      }

      const data = await response.json();
      console.log('Subscription activated:', data);
      
      setIsProcessing(false);
      setPaymentSuccess(true);
      
      // Redirect to dashboard after showing success message for 3 seconds
      setTimeout(() => {
        router.push('/dashboard');
      }, 3000);
    } catch (error) {
      setIsProcessing(false);
      console.error('Payment confirmation error:', error);
      alert(error instanceof Error ? error.message : 'Payment confirmation failed. Please contact support.');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  if (!planDetails) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-lg text-gray-600">Loading payment details...</p>
        </div>
      </div>
    );
  }

  if (paymentSuccess) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full text-center">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <Check className="w-10 h-10 text-green-600" />
          </div>
          <h2 className="text-3xl font-bold text-gray-800 mb-2">Payment Successful!</h2>
          <p className="text-gray-600 mb-4">Your transaction has been processed successfully.</p>
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <p className="text-sm text-gray-500">Amount Paid</p>
            <p className="text-3xl font-bold text-gray-800">${formData.amount}</p>
          </div>
          <p className="text-sm text-gray-500 mb-4">Transaction ID: TXN{Math.random().toString(36).substring(2, 11).toUpperCase()}</p>
          <p className="text-sm text-indigo-600 font-medium animate-pulse">Redirecting to dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white p-4 md:p-8">
      <div className="max-w-2xl mx-auto">
        {/* Back Button */}
        <Button
          variant="ghost"
          className="mb-6 gap-2 text-gray-700"
          onClick={() => router.back()}
        >
          <ArrowLeft className="h-4 w-4" />
          Back 
        </Button>

        {/* Payment Header */}
        <Card className="mb-6 bg-white border-gray-200">
          <CardHeader className="bg-white">
            <CardTitle className="text-gray-800">Complete Your Subscription</CardTitle>
            <CardDescription className="text-gray-600">
              You&apos;re subscribing to the <strong>{planDetails.name}</strong> at{' '}
              <strong>
                ${planDetails.price}/{planDetails.currency === 'USD' ? 'month' : planDetails.currency}
              </strong>
            </CardDescription>
          </CardHeader>
        </Card>

        {/* Payment Form */}
        <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md mx-auto">
          <div className="flex items-center justify-center mb-6">
            <div className="bg-indigo-600 p-3 rounded-full">
              <CreditCard className="w-8 h-8 text-white" />
            </div>
          </div>
          
          <h1 className="text-3xl font-bold text-center text-gray-800 mb-2">Secure Payment</h1>
          <p className="text-center text-gray-600 mb-8 flex items-center justify-center gap-2">
            <Lock className="w-4 h-4" />
            Your information is encrypted and secure
          </p>

          <div className="space-y-6" onKeyDown={handleKeyDown}>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Amount
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 text-lg">$</span>
                <input
                  type="text"
                  name="amount"
                  value={formData.amount}
                  readOnly
                  className="w-full pl-10 pr-4 py-3 border-2 border-gray-200 rounded-lg focus:border-indigo-600 focus:outline-none text-lg font-semibold bg-white text-gray-800"
                  placeholder="0.00"
                />
              </div>
              {errors.amount && (
                <p className="text-red-500 text-sm mt-1 flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  {errors.amount}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Card Number
              </label>
              <input
                type="text"
                name="cardNumber"
                value={formData.cardNumber}
                onChange={handleInputChange}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-indigo-600 focus:outline-none bg-white text-gray-800"
                placeholder="1234 5678 9012 3456"
              />
              {errors.cardNumber && (
                <p className="text-red-500 text-sm mt-1 flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  {errors.cardNumber}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Cardholder Name
              </label>
              <input
                type="text"
                name="cardName"
                value={formData.cardName}
                onChange={handleInputChange}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-indigo-600 focus:outline-none bg-white text-gray-800"
                placeholder="John Doe"
              />
              {errors.cardName && (
                <p className="text-red-500 text-sm mt-1 flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  {errors.cardName}
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Expiry Date
                </label>
                <input
                  type="text"
                  name="expiryDate"
                  value={formData.expiryDate}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-indigo-600 focus:outline-none bg-white text-gray-800"
                  placeholder="MM/YY"
                />
                {errors.expiryDate && (
                  <p className="text-red-500 text-sm mt-1 flex items-center gap-1">
                    <AlertCircle className="w-4 h-4" />
                    {errors.expiryDate}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  CVV
                </label>
                <input
                  type="password"
                  name="cvv"
                  value={formData.cvv}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-indigo-600 focus:outline-none bg-white text-gray-800"
                  placeholder="123"
                />
                {errors.cvv && (
                  <p className="text-red-500 text-sm mt-1 flex items-center gap-1">
                    <AlertCircle className="w-4 h-4" />
                    {errors.cvv}
                  </p>
                )}
              </div>
            </div>

            <button
              type="button"
              onClick={handleSubmit}
              disabled={isProcessing}
              className="w-full bg-yellow-500 text-white py-4 rounded-lg font-semibold text-lg hover:bg-yellow-600 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isProcessing ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Lock className="w-5 h-5" />
                  Pay ${formData.amount}
                </>
              )}
            </button>
          </div>

          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-xs text-center text-gray-500">
              Protected by 256-bit SSL encryption
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function PaymentPage() {
  return (
    <SearchParamsWrapper fallback={<div className="min-h-screen bg-white flex items-center justify-center"><div className="text-center"><p className="text-lg text-gray-600">Loading payment details...</p></div></div>}>
      {(searchParams) => <PaymentPageContent searchParams={searchParams} />}
    </SearchParamsWrapper>
  );
}
