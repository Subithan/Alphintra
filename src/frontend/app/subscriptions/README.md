# Subscriptions Feature

## Overview
The subscriptions feature provides a comprehensive pricing and subscription management system for the Alphintra trading engine. Users can choose between different subscription tiers to access the trading platform's features.

## Current Plans

### Pro Plan - $20/month
**Status:** Active ✅

Perfect for individual traders and small teams with the following features:
- Up to 1 active trading strategy
- Real-time market data
- Advanced technical indicators
- Automated strategy execution
- Backtesting with 2 years of historical data
- Mobile app access
- Portfolio analytics
- Single exchange support

### Max Plan - $200/month
**Status:** Coming Soon 🔒

Ultimate power for professional traders and institutions:
- Unlimited active trading strategies
- Unlimited API calls
- Real-time market data
- Advanced technical indicators
- Automated strategy execution
- Backtesting with 10 years of historical data
- Priority support (1h response)
- Mobile app access
- Advanced risk management & hedging
- Portfolio analytics & reporting
- Multi-exchange support (unlimited)
- Custom webhooks & integrations
- Dedicated account manager
- Advanced AI insights & predictions
- White-label options
- Custom indicator development

## Components

### SubscriptionCard
Displays individual subscription plan details with pricing, features, and a subscribe button.

**Props:**
- `plan: SubscriptionPlan` - The subscription plan data
- `onSubscribe?: (planId: string) => void` - Callback when user clicks subscribe
- `isLoading?: boolean` - Loading state during subscription
- `currentPlan?: string` - ID of the user's current plan

**Features:**
- Responsive design
- Popular plan highlighting
- Coming soon badge for disabled plans
- Current plan indicator
- Feature list with included/excluded states
- Animated hover effects

### SubscriptionComparison
Shows a detailed comparison table between different plans.

**Props:**
- `features: ComparisonFeature[]` - Array of features to compare

**Features:**
- Responsive table layout
- Feature descriptions
- Visual indicators (checkmarks/crosses)
- Zebra striping for better readability

### SubscriptionHeader
Marketing header with platform benefits.

**Features:**
- Gradient title text
- Key benefits display with icons
- Responsive grid layout

### SubscriptionFAQ
Frequently asked questions section with additional information.

**Features:**
- Common questions about subscriptions
- "What's Included" vs "Not Included" cards
- Hover effects on FAQ cards

### PricingToggle
Toggle between monthly and yearly billing (for future use).

**Props:**
- `interval: 'month' | 'year'` - Current billing interval
- `onIntervalChange: (interval) => void` - Callback when interval changes
- `className?: string` - Additional CSS classes

## Page Structure

### /subscriptions (page.tsx)
Main subscription page with:
- Marketing header
- Subscription plan cards
- Toggle for detailed comparison
- FAQ section
- Trust indicators

## Styling

The subscription components use:
- Tailwind CSS for utility classes
- shadcn/ui components (Card, Badge, Button)
- Responsive design (mobile-first)
- Gradient accents for premium feel
- Smooth transitions and hover effects

## State Management

The page manages:
- Selected billing interval (for future yearly pricing)
- Loading states during subscription process
- Current user plan
- Comparison table visibility

## API Integration

### TODO: Implement
The subscription flow requires these API endpoints:

```typescript
// Create subscription
POST /api/subscriptions/create
Body: { planId: string }
Response: { checkoutUrl: string }

// Get current subscription
GET /api/subscriptions/current
Response: { planId: string, status: string, expiresAt: string }

// Cancel subscription
POST /api/subscriptions/cancel
Body: { planId: string }
Response: { success: boolean }

// Update subscription
POST /api/subscriptions/update
Body: { newPlanId: string }
Response: { success: boolean }
```

## Payment Integration

### Recommended: Stripe
Integrate Stripe for payment processing:

1. Install Stripe SDK:
```bash
npm install @stripe/stripe-js stripe
```

2. Create checkout session endpoint
3. Handle webhook events for subscription updates
4. Update user subscription status in database

## Future Enhancements

- [ ] Yearly billing with discount
- [ ] Custom enterprise plans
- [ ] Usage analytics dashboard
- [ ] Subscription upgrade/downgrade flow
- [ ] Trial period management
- [ ] Promo code support
- [ ] Multiple payment methods
- [ ] Invoice history
- [ ] Team member management
- [ ] Usage alerts and notifications

## File Structure

```
src/frontend/
├── app/
│   └── subscriptions/
│       ├── page.tsx           # Main subscriptions page
│       └── layout.tsx         # Layout with metadata
└── components/
    └── subscriptions/
        ├── SubscriptionCard.tsx
        ├── SubscriptionComparison.tsx
        ├── SubscriptionHeader.tsx
        ├── SubscriptionFAQ.tsx
        ├── PricingToggle.tsx
        └── index.ts           # Exports
```

## Usage Example

```typescript
import { SubscriptionCard } from '@/components/subscriptions';

const plan = {
  id: 'pro',
  name: 'Pro',
  price: 20,
  currency: 'USD',
  interval: 'month',
  description: 'Perfect for individual traders',
  features: [
    { text: 'Feature 1', included: true },
    { text: 'Feature 2', included: false },
  ],
};

function MyComponent() {
  const handleSubscribe = (planId: string) => {
    // Handle subscription
  };

  return (
    <SubscriptionCard
      plan={plan}
      onSubscribe={handleSubscribe}
      currentPlan="basic"
    />
  );
}
```

## Accessibility

All components include:
- Semantic HTML
- ARIA labels where appropriate
- Keyboard navigation support
- Focus indicators
- Screen reader friendly

## Testing

To test the subscription page:

1. Navigate to `/subscriptions`
2. Verify both plans are displayed
3. Check that Pro plan shows "Most Popular" badge
4. Check that Max plan shows "Coming Soon" badge and disabled button
5. Click "Show Detailed Comparison" to view comparison table
6. Review FAQ section
7. Test subscribe button (currently shows toast notification)

## Notes

- The Max plan is currently disabled with a "Coming Soon" badge
- Subscription API integration is pending implementation
- Payment processing needs to be configured
- User authentication should be verified before allowing subscriptions
