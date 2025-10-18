'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useSubscriptionModal } from '@/contexts/SubscriptionModalContext';

export default function SubscriptionsPage() {
  const router = useRouter();
  const { openModal } = useSubscriptionModal();

  useEffect(() => {
    // Open the modal
    openModal();
    
    // Redirect to home/dashboard after a short delay
    const timer = setTimeout(() => {
      router.push('/dashboard');
    }, 100);

    return () => clearTimeout(timer);
  }, [openModal, router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
        <p className="text-muted-foreground">Opening subscriptions...</p>
      </div>
    </div>
  );
}
