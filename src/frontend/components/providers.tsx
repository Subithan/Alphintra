'use client';

import { ApolloProvider } from '@apollo/client';
import { ThemeProvider } from 'next-themes';
import { apolloClient } from '@/lib/graphql/apollo-client';
import { AuthProvider } from '@/components/auth/auth-provider';
import { UserProvider } from '@/contexts/UserContext';
import { SubscriptionModalProvider } from '@/contexts/SubscriptionModalContext';
import { SubscriptionModal } from '@/components/subscriptions';
import { useSubscriptionModal } from '@/contexts/SubscriptionModalContext';

interface ProvidersProps {
  children: React.ReactNode;
}

function SubscriptionModalWrapper() {
  const { isOpen, closeModal } = useSubscriptionModal();
  return <SubscriptionModal isOpen={isOpen} onClose={closeModal} />;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      <ApolloProvider client={apolloClient}>
        <AuthProvider>
          <UserProvider>
            <SubscriptionModalProvider>
              {children}
              <SubscriptionModalWrapper />
            </SubscriptionModalProvider>
          </UserProvider>
        </AuthProvider>
      </ApolloProvider>
    </ThemeProvider>
  );
}