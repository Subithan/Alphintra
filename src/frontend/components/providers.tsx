'use client';

import { ApolloProvider } from '@apollo/client';
import { ThemeProvider } from 'next-themes';
import { apolloClient } from '@/lib/apollo-client';
import { AuthProvider } from '@/components/auth/auth-provider';

interface ProvidersProps {
  children: React.ReactNode;
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
          {children}
        </AuthProvider>
      </ApolloProvider>
    </ThemeProvider>
  );
}