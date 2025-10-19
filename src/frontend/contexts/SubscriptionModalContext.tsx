'use client';

import React, { createContext, useContext, useState, useCallback } from 'react';

interface SubscriptionModalContextType {
  isOpen: boolean;
  openModal: () => void;
  closeModal: () => void;
}

const SubscriptionModalContext = createContext<SubscriptionModalContextType | undefined>(undefined);

export function SubscriptionModalProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);

  const openModal = useCallback(() => {
    setIsOpen(true);
  }, []);

  const closeModal = useCallback(() => {
    setIsOpen(false);
  }, []);

  return (
    <SubscriptionModalContext.Provider value={{ isOpen, openModal, closeModal }}>
      {children}
    </SubscriptionModalContext.Provider>
  );
}

export function useSubscriptionModal() {
  const context = useContext(SubscriptionModalContext);
  if (context === undefined) {
    throw new Error('useSubscriptionModal must be used within a SubscriptionModalProvider');
  }
  return context;
}
