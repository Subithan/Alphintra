'use client';

import { FormEvent, useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { fetchStrategyById } from '@/app/api/strategyApi';
import { purchaseStrategy } from '@/app/api/paymentApi';
import { Strategy } from '@/components/marketplace/types';
import GradientBorder from '@/components/ui/GradientBorder';
import { Loader2 } from 'lucide-react';

interface CardErrors {
  cardName?: string;
  cardNumber?: string;
  expiry?: string;
  cvv?: string;
}

const initialErrors: CardErrors = {};

export default function MarketplacePurchasePage() {
  const params = useParams();
  const router = useRouter();
  const strategyId = params?.id as string;

  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [strategyError, setStrategyError] = useState<string | null>(null);
  const [loadingStrategy, setLoadingStrategy] = useState(true);

  const [cardName, setCardName] = useState('');
  const [cardNumber, setCardNumber] = useState('');
  const [expiry, setExpiry] = useState('');
  const [cvv, setCvv] = useState('');
  const [errors, setErrors] = useState<CardErrors>(initialErrors);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function loadStrategy() {
      setLoadingStrategy(true);
      const data = await fetchStrategyById(strategyId);
      if (cancelled) return;
      if (!data) {
        setStrategyError('Unable to find the selected strategy.');
      } else {
        setStrategy(data);
        setStrategyError(null);
      }
      setLoadingStrategy(false);
    }
    loadStrategy();
    return () => {
      cancelled = true;
    };
  }, [strategyId]);

  const validate = (): boolean => {
    const nextErrors: CardErrors = {};

    if (!cardName.trim()) {
      nextErrors.cardName = 'Cardholder name is required.';
    }

    const sanitizedNumber = cardNumber.replace(/\s+/g, '');
    if (!/^\d{16}$/.test(sanitizedNumber)) {
      nextErrors.cardNumber = 'Card number must be 16 digits.';
    }

    const expiryRegex = /^(0[1-9]|1[0-2])\/\d{2}$/;
    if (!expiryRegex.test(expiry)) {
      nextErrors.expiry = 'Expiry must be in MM/YY format.';
    } else {
      const [month, year] = expiry.split('/').map((v) => parseInt(v, 10));
      const current = new Date();
      const expiryDate = new Date(2000 + year, month - 1, 1);
      expiryDate.setMonth(expiryDate.getMonth() + 1); // end of month
      if (expiryDate < current) {
        nextErrors.expiry = 'Card has expired.';
      }
    }

    if (!/^\d{3,4}$/.test(cvv)) {
      nextErrors.cvv = 'CVV must be 3 or 4 digits.';
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!strategy) return;

    if (!validate()) return;

    setIsSubmitting(true);
    setSubmitError(null);
    try {
      await purchaseStrategy(strategy.id, {
        notes: `User purchase of strategy ${strategy.name}`,
      });
      setSubmitSuccess('Payment successful! Redirecting back to marketplace…');
      setTimeout(() => router.push('/marketplace'), 1500);
    } catch (err) {
      setSubmitError((err as Error).message ?? 'Failed to complete purchase.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const formattedPrice =
    strategy && strategy.price !== 'free'
      ? `$${strategy.price.toFixed(2)}`
      : 'Free';

  if (loadingStrategy) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background text-foreground">
        <p className="text-lg text-muted-foreground">Loading checkout…</p>
      </div>
    );
  }

  if (strategyError || !strategy) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background text-foreground">
        <div className="max-w-md text-center space-y-4">
          <h1 className="text-2xl font-semibold">Unable to load strategy</h1>
          <p className="text-muted-foreground">
            {strategyError ?? 'Please return to the marketplace and try again.'}
          </p>
          <button
            className="bg-yellow-500 hover:bg-yellow-600 text-black px-4 py-2 rounded-lg transition-colors"
            onClick={() => router.push('/marketplace')}
          >
            Back to Marketplace
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="max-w-3xl mx-auto py-12 px-4 space-y-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Complete purchase</h1>
          <p className="text-muted-foreground">
            Confirm your payment details to unlock <strong>{strategy.name}</strong>.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <GradientBorder gradientAngle="135deg" className="p-6 space-y-4">
            <h2 className="text-xl font-semibold">Order summary</h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Strategy</span>
                <span className="font-medium">{strategy.name}</span>
              </div>
              <div className="flex justify-between">
                <span>Creator</span>
                <span>{strategy.creatorName}</span>
              </div>
              <div className="flex justify-between">
                <span>Subscribers</span>
                <span>{strategy.subscriberCount}</span>
              </div>
              <div className="flex justify-between">
                <span>Risk level</span>
                <span className="capitalize">{strategy.riskLevel}</span>
              </div>
              <div className="flex justify-between text-base font-semibold pt-2">
                <span>Total</span>
                <span>{formattedPrice}</span>
              </div>
            </div>
          </GradientBorder>

          <GradientBorder gradientAngle="225deg" className="p-6 space-y-4">
            <h2 className="text-xl font-semibold">Payment details</h2>
            <form className="space-y-4" onSubmit={handleSubmit} noValidate>
              <div>
                <label className="block text-sm font-medium mb-1">
                  Cardholder name
                </label>
                <input
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  type="text"
                  value={cardName}
                  onChange={(e) => setCardName(e.target.value)}
                  placeholder="Jane Doe"
                />
                {errors.cardName && (
                  <p className="mt-1 text-xs text-red-500">{errors.cardName}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Card number
                </label>
                <input
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  type="text"
                  inputMode="numeric"
                  value={cardNumber}
                  onChange={(e) => setCardNumber(e.target.value)}
                  placeholder="0000 0000 0000 0000"
                />
                {errors.cardNumber && (
                  <p className="mt-1 text-xs text-red-500">{errors.cardNumber}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Expiry (MM/YY)
                  </label>
                  <input
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    type="text"
                    inputMode="numeric"
                    value={expiry}
                    onChange={(e) => setExpiry(e.target.value)}
                    placeholder="04/27"
                  />
                  {errors.expiry && (
                    <p className="mt-1 text-xs text-red-500">{errors.expiry}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">CVV</label>
                  <input
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    type="password"
                    inputMode="numeric"
                    value={cvv}
                    onChange={(e) => setCvv(e.target.value)}
                    placeholder="123"
                  />
                  {errors.cvv && (
                    <p className="mt-1 text-xs text-red-500">{errors.cvv}</p>
                  )}
                </div>
              </div>

              {submitError && (
                <p className="text-sm text-red-500">{submitError}</p>
              )}
              {submitSuccess && (
                <p className="text-sm text-green-500">{submitSuccess}</p>
              )}

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full inline-flex items-center justify-center gap-2 bg-yellow-500 hover:bg-yellow-600 text-black font-semibold py-3 rounded-lg transition-colors disabled:opacity-70 disabled:cursor-not-allowed"
              >
                {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
                Pay now {formattedPrice !== 'Free' && formattedPrice !== '$0.00' ? formattedPrice : ''}
              </button>
            </form>
          </GradientBorder>
        </div>
      </div>
    </div>
  );
}
