import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Subscriptions - Trading Engine Plans',
  description: 'Choose the perfect trading engine subscription plan for your needs. Pro and Max plans available with advanced features for automated trading.',
  keywords: ['trading subscription', 'trading plans', 'algorithmic trading', 'trading engine', 'automated trading'],
};

export default function SubscriptionsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
