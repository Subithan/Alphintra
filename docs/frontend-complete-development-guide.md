# Alphintra Frontend - Complete Development Guide

## Table of Contents
1. [Project Structure Deep Dive](#project-structure-deep-dive)
2. [Next.js App Router - Complete Guide](#nextjs-app-router-complete-guide)
3. [File System Routing](#file-system-routing)
4. [Creating New Pages Step-by-Step](#creating-new-pages-step-by-step)
5. [Layout System Explained](#layout-system-explained)
6. [Component Development from Scratch](#component-development-from-scratch)
7. [Design System Implementation](#design-system-implementation)
8. [Styling - Complete Workflow](#styling-complete-workflow)
9. [State Management Deep Dive](#state-management-deep-dive)
10. [Authentication Implementation](#authentication-implementation)
11. [GraphQL Integration Step-by-Step](#graphql-integration-step-by-step)
12. [How Every Code File Works](#how-every-code-file-works)
13. [Development Workflow](#development-workflow)
14. [Advanced Patterns](#advanced-patterns)
15. [Real-World Examples](#real-world-examples)

---

## Project Structure Deep Dive

### Understanding the File System

```
src/frontend/
├── app/                          # Next.js 14+ App Router (NEW)
│   ├── globals.css              # Global styles - imported in layout.tsx
│   ├── layout.tsx               # Root layout - wraps all pages
│   ├── page.tsx                 # Home page (/) - the landing page
│   ├── loading.tsx              # Loading UI for the entire app
│   ├── error.tsx                # Error UI for the entire app
│   ├── not-found.tsx            # 404 page
│   │
│   ├── (auth)/                  # Route Group - doesn't affect URL
│   │   ├── layout.tsx           # Auth layout - only for auth pages
│   │   ├── login/
│   │   │   ├── page.tsx         # /login page
│   │   │   └── loading.tsx      # Loading UI for login
│   │   ├── register/
│   │   │   └── page.tsx         # /register page
│   │   └── forgot-password/
│   │       └── page.tsx         # /forgot-password page
│   │
│   └── (dashboard)/             # Route Group - requires authentication
│       ├── layout.tsx           # Dashboard layout
│       ├── dashboard/
│       │   ├── page.tsx         # /dashboard page
│       │   └── loading.tsx      # Dashboard loading UI
│       ├── strategies/
│       │   ├── page.tsx         # /strategies page
│       │   ├── [id]/
│       │   │   ├── page.tsx     # /strategies/[id] - dynamic route
│       │   │   └── edit/
│       │   │       └── page.tsx # /strategies/[id]/edit
│       │   └── create/
│       │       └── page.tsx     # /strategies/create
│       └── settings/
│           ├── page.tsx         # /settings page
│           ├── profile/
│           │   └── page.tsx     # /settings/profile
│           └── api-keys/
│               └── page.tsx     # /settings/api-keys
│
├── components/                   # React Components
│   ├── ui/                      # Reusable UI components
│   │   ├── button.tsx           # Button component
│   │   ├── input.tsx            # Input component
│   │   ├── modal.tsx            # Modal component
│   │   ├── toaster.tsx          # Toast notifications
│   │   └── index.ts             # Export all UI components
│   │
│   ├── auth/                    # Authentication components
│   │   ├── auth-provider.tsx    # Auth context provider
│   │   ├── login-form.tsx       # Login form component
│   │   ├── register-form.tsx    # Registration form
│   │   └── protected-route.tsx  # Route protection
│   │
│   ├── trading/                 # Trading-specific components
│   │   ├── portfolio-summary.tsx
│   │   ├── strategy-card.tsx
│   │   ├── market-data-widget.tsx
│   │   └── trading-chart.tsx
│   │
│   ├── layout/                  # Layout components
│   │   ├── header.tsx           # App header
│   │   ├── sidebar.tsx          # Dashboard sidebar
│   │   ├── footer.tsx           # App footer
│   │   └── breadcrumb.tsx       # Breadcrumb navigation
│   │
│   ├── landing/                 # Landing page components
│   │   ├── landing-page.tsx     # Main landing page
│   │   ├── hero-section.tsx     # Hero section
│   │   ├── features-section.tsx # Features section
│   │   └── pricing-section.tsx  # Pricing section
│   │
│   └── providers.tsx            # Global providers wrapper
│
├── lib/                         # Utility libraries and configurations
│   ├── stores/                  # Zustand state stores
│   │   ├── auth-store.ts        # Authentication state
│   │   ├── trading-store.ts     # Trading data state
│   │   └── ui-store.ts          # UI state (modals, themes, etc.)
│   │
│   ├── hooks/                   # Custom React hooks
│   │   ├── use-auth.ts          # Authentication hook
│   │   ├── use-trading.ts       # Trading data hook
│   │   └── use-local-storage.ts # Local storage hook
│   │
│   ├── utils/                   # Utility functions
│   │   ├── index.ts             # Main utilities (cn, formatters)
│   │   ├── validation.ts        # Form validation schemas
│   │   ├── api.ts               # API client functions
│   │   └── constants.ts         # App constants
│   │
│   ├── types/                   # TypeScript type definitions
│   │   ├── auth.ts              # Authentication types
│   │   ├── trading.ts           # Trading data types
│   │   └── api.ts               # API response types
│   │
│   ├── apollo-client.ts         # GraphQL client configuration
│   ├── auth.ts                  # Authentication utilities
│   └── env.ts                   # Environment variables validation
│
├── public/                      # Static assets
│   ├── images/                  # Image assets
│   ├── icons/                   # Icon files
│   ├── favicon.ico              # Favicon
│   └── robots.txt               # SEO robots file
│
├── styles/                      # Additional stylesheets (if needed)
│   └── components.css           # Component-specific styles
│
├── package.json                 # Dependencies and scripts
├── tailwind.config.ts           # Tailwind CSS configuration
├── tsconfig.json               # TypeScript configuration
├── next.config.js              # Next.js configuration
└── .env.local                  # Environment variables
```

---

## Next.js App Router - Complete Guide

### Understanding App Router vs Pages Router

**App Router (NEW - We're using this):**
- File-based routing using `app/` directory
- Server Components by default
- Nested layouts
- Built-in loading and error states
- Route groups for organization

### How Routing Works

#### 1. Basic Page Creation
```typescript
// app/about/page.tsx
export default function AboutPage() {
  return (
    <div>
      <h1>About Us</h1>
      <p>This is the about page</p>
    </div>
  );
}
```
**Result:** Creates `/about` route

#### 2. Nested Routes
```typescript
// app/products/shoes/page.tsx
export default function ShoesPage() {
  return <div>Shoes Page</div>;
}
```
**Result:** Creates `/products/shoes` route

#### 3. Dynamic Routes
```typescript
// app/strategies/[id]/page.tsx
interface Props {
  params: { id: string };
}

export default function StrategyPage({ params }: Props) {
  return (
    <div>
      <h1>Strategy ID: {params.id}</h1>
    </div>
  );
}
```
**Result:** Creates `/strategies/123`, `/strategies/abc`, etc.

#### 4. Catch-All Routes
```typescript
// app/docs/[...slug]/page.tsx
interface Props {
  params: { slug: string[] };
}

export default function DocsPage({ params }: Props) {
  return (
    <div>
      <h1>Docs: {params.slug.join('/')}</h1>
    </div>
  );
}
```
**Result:** Creates `/docs/a`, `/docs/a/b`, `/docs/a/b/c`, etc.

#### 5. Route Groups (Don't affect URL)
```typescript
// app/(marketing)/about/page.tsx - URL: /about
// app/(marketing)/contact/page.tsx - URL: /contact
// app/(dashboard)/profile/page.tsx - URL: /profile

// Each group can have its own layout
// app/(marketing)/layout.tsx - only applies to marketing pages
// app/(dashboard)/layout.tsx - only applies to dashboard pages
```

---

## File System Routing

### Special Files in App Router

#### 1. `page.tsx` - The actual page component
```typescript
// app/dashboard/page.tsx
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Dashboard - Alphintra',
  description: 'Your trading dashboard',
};

export default function DashboardPage() {
  return (
    <div>
      <h1>Dashboard</h1>
      {/* Page content */}
    </div>
  );
}
```

#### 2. `layout.tsx` - Shared layout for routes
```typescript
// app/dashboard/layout.tsx
import { Sidebar } from '@/components/layout/sidebar';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
```

#### 3. `loading.tsx` - Loading UI
```typescript
// app/dashboard/loading.tsx
export default function DashboardLoading() {
  return (
    <div className="flex items-center justify-center h-screen">
      <div className="loading-spinner w-8 h-8"></div>
    </div>
  );
}
```

#### 4. `error.tsx` - Error UI
```typescript
// app/dashboard/error.tsx
'use client'; // Error components must be Client Components

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center h-screen">
      <h2>Something went wrong!</h2>
      <button onClick={reset}>Try again</button>
    </div>
  );
}
```

#### 5. `not-found.tsx` - 404 page
```typescript
// app/dashboard/not-found.tsx
export default function DashboardNotFound() {
  return (
    <div>
      <h2>Page Not Found</h2>
      <p>Could not find the requested page.</p>
    </div>
  );
}
```

---

## Creating New Pages Step-by-Step

### Example 1: Creating a Simple Page

**Step 1:** Create the directory structure
```bash
mkdir -p app/pricing
```

**Step 2:** Create the page file
```typescript
// app/pricing/page.tsx
import { Metadata } from 'next';
import { PricingSection } from '@/components/pricing/pricing-section';

export const metadata: Metadata = {
  title: 'Pricing - Alphintra',
  description: 'Choose the perfect plan for your trading needs',
  keywords: ['pricing', 'plans', 'subscription', 'trading'],
};

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-center mb-8">
          Choose Your Plan
        </h1>
        <PricingSection />
      </div>
    </div>
  );
}
```

**Step 3:** Create the component
```typescript
// components/pricing/pricing-section.tsx
import { Button } from '@/components/ui/button';

const plans = [
  {
    name: 'Basic',
    price: '$29',
    features: ['5 Strategies', 'Basic Analytics', 'Email Support'],
  },
  {
    name: 'Pro',
    price: '$99',
    features: ['Unlimited Strategies', 'Advanced Analytics', 'Priority Support'],
  },
];

export function PricingSection() {
  return (
    <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
      {plans.map((plan) => (
        <div key={plan.name} className="trading-card p-6">
          <h3 className="text-2xl font-bold mb-4">{plan.name}</h3>
          <div className="text-3xl font-bold mb-6">{plan.price}/month</div>
          <ul className="space-y-2 mb-6">
            {plan.features.map((feature) => (
              <li key={feature} className="flex items-center">
                <span className="text-profit mr-2">✓</span>
                {feature}
              </li>
            ))}
          </ul>
          <Button className="w-full">Get Started</Button>
        </div>
      ))}
    </div>
  );
}
```

**Result:** You now have a `/pricing` page with a custom component!

### Example 2: Creating a Dynamic Page with Data Fetching

**Step 1:** Create the directory structure
```bash
mkdir -p app/strategies/[id]
```

**Step 2:** Create the dynamic page
```typescript
// app/strategies/[id]/page.tsx
import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { StrategyDetails } from '@/components/trading/strategy-details';

interface Props {
  params: { id: string };
}

// Generate metadata dynamically
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const strategy = await getStrategy(params.id);
  
  if (!strategy) {
    return {
      title: 'Strategy Not Found',
    };
  }

  return {
    title: `${strategy.name} - Strategy Details`,
    description: strategy.description,
  };
}

async function getStrategy(id: string) {
  // This would typically fetch from your API
  const strategies = [
    { id: '1', name: 'Moving Average Strategy', description: 'A simple MA strategy' },
    { id: '2', name: 'RSI Strategy', description: 'RSI-based trading strategy' },
  ];
  
  return strategies.find(s => s.id === id);
}

export default async function StrategyPage({ params }: Props) {
  const strategy = await getStrategy(params.id);
  
  if (!strategy) {
    notFound(); // This will show the not-found.tsx page
  }
  
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">{strategy.name}</h1>
      <StrategyDetails strategy={strategy} />
    </div>
  );
}
```

**Step 3:** Create the component
```typescript
// components/trading/strategy-details.tsx
interface Strategy {
  id: string;
  name: string;
  description: string;
}

interface Props {
  strategy: Strategy;
}

export function StrategyDetails({ strategy }: Props) {
  return (
    <div className="trading-card p-6">
      <h2 className="text-xl font-semibold mb-4">Strategy Details</h2>
      <p className="text-muted-foreground mb-4">{strategy.description}</p>
      
      <div className="grid md:grid-cols-2 gap-4">
        <div className="metric-card">
          <h3 className="font-semibold">Total Return</h3>
          <p className="text-2xl profit-text">+15.3%</p>
        </div>
        <div className="metric-card">
          <h3 className="font-semibold">Sharpe Ratio</h3>
          <p className="text-2xl">1.85</p>
        </div>
      </div>
    </div>
  );
}
```

**Result:** You now have `/strategies/1`, `/strategies/2`, etc. pages with dynamic content!

---

## Layout System Explained

### Understanding Layout Hierarchy

Layouts in Next.js App Router are nested and hierarchical:

```
app/layout.tsx                 # Root layout (applies to ALL pages)
├── app/page.tsx              # Home page
├── app/(auth)/layout.tsx     # Auth layout (only auth pages)
│   ├── app/(auth)/login/page.tsx
│   └── app/(auth)/register/page.tsx
└── app/(dashboard)/layout.tsx # Dashboard layout (only dashboard pages)
    ├── app/(dashboard)/dashboard/page.tsx
    └── app/(dashboard)/strategies/page.tsx
```

### Root Layout (Required)

```typescript
// app/layout.tsx
import type { Metadata } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { Providers } from '@/components/providers';
import { Toaster } from '@/components/ui/toaster';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
});

export const metadata: Metadata = {
  title: {
    default: 'Alphintra - AI-Powered Trading Platform',
    template: '%s | Alphintra', // %s will be replaced by page titles
  },
  description: 'Professional AI-powered trading platform',
  // ... other metadata
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="min-h-screen bg-background font-sans antialiased">
        <Providers>
          {children}
          <Toaster />
        </Providers>
      </body>
    </html>
  );
}
```

### Authentication Layout

```typescript
// app/(auth)/layout.tsx
import { AuthBackground } from '@/components/auth/auth-background';

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex">
      {/* Left side - Auth form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {children}
        </div>
      </div>
      
      {/* Right side - Background/branding */}
      <div className="hidden lg:flex lg:flex-1">
        <AuthBackground />
      </div>
    </div>
  );
}
```

### Dashboard Layout

```typescript
// app/(dashboard)/layout.tsx
import { Sidebar } from '@/components/layout/sidebar';
import { Header } from '@/components/layout/header';
import { ProtectedRoute } from '@/components/auth/protected-route';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute>
      <div className="h-screen flex">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          <main className="flex-1 overflow-auto p-6">
            {children}
          </main>
        </div>
      </div>
    </ProtectedRoute>
  );
}
```

---

## Component Development from Scratch

### Step 1: Planning Your Component

Before writing code, plan your component:
- What props does it need?
- What state does it manage?
- How will it be styled?
- What interactions does it support?

### Step 2: Creating a Basic Component

```typescript
// components/ui/card.tsx
import React from 'react';
import { cn } from '@/lib/utils';

// 1. Define the interface for props
interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'outlined' | 'elevated';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
}

// 2. Create the component
export function Card({ 
  variant = 'default', 
  size = 'md',
  className,
  children,
  ...props 
}: CardProps) {
  return (
    <div
      className={cn(
        // Base styles
        'rounded-lg border bg-card text-card-foreground shadow-sm',
        
        // Variant styles
        {
          'border-border': variant === 'default',
          'border-2 border-primary': variant === 'outlined',
          'shadow-lg': variant === 'elevated',
        },
        
        // Size styles
        {
          'p-3': size === 'sm',
          'p-4': size === 'md',
          'p-6': size === 'lg',
        },
        
        // Allow custom className
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

// 3. Create sub-components for composition
export function CardHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('flex flex-col space-y-1.5 pb-4', className)}
      {...props}
    />
  );
}

export function CardTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn('text-lg font-semibold leading-none tracking-tight', className)}
      {...props}
    />
  );
}

export function CardContent({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('pt-0', className)} {...props} />
  );
}

export function CardFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('flex items-center pt-4', className)} {...props} />
  );
}
```

### Step 3: Using the Component

```typescript
// Example usage in a page
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function ExamplePage() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <Card variant="outlined" size="lg">
        <CardHeader>
          <CardTitle>Strategy Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Your strategy has performed well this month.
          </p>
        </CardContent>
        <CardFooter>
          <Button>View Details</Button>
        </CardFooter>
      </Card>
    </div>
  );
}
```

### Step 4: Advanced Component with State

```typescript
// components/trading/strategy-card.tsx
'use client';

import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PlayCircle, PauseCircle, StopCircle } from 'lucide-react';

interface Strategy {
  id: string;
  name: string;
  description: string;
  status: 'ACTIVE' | 'PAUSED' | 'STOPPED';
  totalReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
}

interface StrategyCardProps {
  strategy: Strategy;
  onStatusChange: (id: string, status: Strategy['status']) => void;
}

export function StrategyCard({ strategy, onStatusChange }: StrategyCardProps) {
  const [isLoading, setIsLoading] = useState(false);
  
  const handleStatusChange = async (newStatus: Strategy['status']) => {
    setIsLoading(true);
    try {
      await onStatusChange(strategy.id, newStatus);
    } finally {
      setIsLoading(false);
    }
  };
  
  const getStatusColor = (status: Strategy['status']) => {
    switch (status) {
      case 'ACTIVE': return 'profit';
      case 'PAUSED': return 'warning';
      case 'STOPPED': return 'loss';
    }
  };
  
  const getStatusIcon = (status: Strategy['status']) => {
    switch (status) {
      case 'ACTIVE': return PlayCircle;
      case 'PAUSED': return PauseCircle;
      case 'STOPPED': return StopCircle;
    }
  };
  
  const StatusIcon = getStatusIcon(strategy.status);
  
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl">{strategy.name}</CardTitle>
          <Badge variant={getStatusColor(strategy.status)}>
            <StatusIcon className="w-3 h-3 mr-1" />
            {strategy.status}
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          {strategy.description}
        </p>
      </CardHeader>
      
      <CardContent>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-sm text-muted-foreground">Total Return</p>
            <p className={`text-lg font-semibold ${
              strategy.totalReturn >= 0 ? 'profit-text' : 'loss-text'
            }`}>
              {strategy.totalReturn >= 0 ? '+' : ''}{strategy.totalReturn.toFixed(2)}%
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Sharpe Ratio</p>
            <p className="text-lg font-semibold">{strategy.sharpeRatio.toFixed(2)}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Max Drawdown</p>
            <p className="text-lg font-semibold loss-text">
              -{strategy.maxDrawdown.toFixed(2)}%
            </p>
          </div>
        </div>
      </CardContent>
      
      <CardFooter className="flex gap-2">
        {strategy.status === 'STOPPED' && (
          <Button 
            size="sm" 
            onClick={() => handleStatusChange('ACTIVE')}
            disabled={isLoading}
          >
            Start
          </Button>
        )}
        {strategy.status === 'ACTIVE' && (
          <Button 
            size="sm" 
            variant="outline"
            onClick={() => handleStatusChange('PAUSED')}
            disabled={isLoading}
          >
            Pause
          </Button>
        )}
        {strategy.status === 'PAUSED' && (
          <>
            <Button 
              size="sm"
              onClick={() => handleStatusChange('ACTIVE')}
              disabled={isLoading}
            >
              Resume
            </Button>
            <Button 
              size="sm" 
              variant="destructive"
              onClick={() => handleStatusChange('STOPPED')}
              disabled={isLoading}
            >
              Stop
            </Button>
          </>
        )}
      </CardFooter>
    </Card>
  );
}
```

---

## Design System Implementation

### Understanding Our Design System

Our design system is built with Tailwind CSS and consists of:
1. **Color Palette** - Defined in `tailwind.config.ts`
2. **Typography** - Font families and sizes
3. **Spacing** - Consistent spacing scale
4. **Components** - Reusable UI components
5. **Utilities** - CSS utility classes

### Color System Deep Dive

```typescript
// tailwind.config.ts
const config = {
  theme: {
    extend: {
      colors: {
        // Base colors from CSS variables
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: 'hsl(var(--primary))',
        secondary: 'hsl(var(--secondary))',
        
        // Trading-specific colors
        profit: {
          DEFAULT: 'hsl(142, 76%, 36%)',  // Green for profits
          light: 'hsl(142, 76%, 46%)',
          dark: 'hsl(142, 76%, 26%)',
        },
        loss: {
          DEFAULT: 'hsl(0, 84%, 60%)',    // Red for losses
          light: 'hsl(0, 84%, 70%)',
          dark: 'hsl(0, 84%, 50%)',
        },
        warning: {
          DEFAULT: 'hsl(38, 92%, 50%)',   // Orange for warnings
          light: 'hsl(38, 92%, 60%)',
          dark: 'hsl(38, 92%, 40%)',
        },
      },
    },
  },
};
```

### Using Colors in Components

```typescript
// Example: Profit/Loss indicator
export function ProfitLossDisplay({ value }: { value: number }) {
  return (
    <span className={`font-semibold ${
      value >= 0 
        ? 'text-profit bg-profit/10 border-profit/20' 
        : 'text-loss bg-loss/10 border-loss/20'
    } px-2 py-1 rounded border`}>
      {value >= 0 ? '+' : ''}{value.toFixed(2)}%
    </span>
  );
}
```

### Typography System

```css
/* globals.css - Typography utilities */
.text-display-1 { @apply text-4xl font-bold tracking-tight; }
.text-display-2 { @apply text-3xl font-bold tracking-tight; }
.text-heading-1 { @apply text-2xl font-semibold; }
.text-heading-2 { @apply text-xl font-semibold; }
.text-heading-3 { @apply text-lg font-semibold; }
.text-body-1 { @apply text-base; }
.text-body-2 { @apply text-sm; }
.text-caption { @apply text-xs text-muted-foreground; }
```

### Component Styling Patterns

```typescript
// Pattern 1: Base component with variants
export function Alert({ variant = 'default', children }: AlertProps) {
  return (
    <div className={cn(
      // Base styles
      'rounded-lg border p-4',
      
      // Variant styles
      {
        'bg-background text-foreground': variant === 'default',
        'bg-profit/10 text-profit border-profit/20': variant === 'success',
        'bg-loss/10 text-loss border-loss/20': variant === 'error',
        'bg-warning/10 text-warning border-warning/20': variant === 'warning',
      }
    )}>
      {children}
    </div>
  );
}
```

### Creating Custom Utilities

```css
/* globals.css - Custom trading utilities */
@layer components {
  .trading-card {
    @apply bg-card border border-border rounded-lg shadow-sm p-4 
           hover:shadow-md transition-shadow duration-200;
  }
  
  .metric-display {
    @apply text-center p-4 rounded-lg bg-muted/50;
  }
  
  .profit-indicator {
    @apply text-profit font-semibold;
  }
  
  .loss-indicator {
    @apply text-loss font-semibold;
  }
  
  .status-badge {
    @apply inline-flex items-center px-2 py-1 rounded-full text-xs font-medium;
  }
  
  .status-active {
    @apply status-badge bg-profit/10 text-profit border border-profit/20;
  }
  
  .status-inactive {
    @apply status-badge bg-muted text-muted-foreground border border-border;
  }
}
```

---

## Styling - Complete Workflow

### Step 1: Understanding the CSS Architecture

```
styles/
├── globals.css              # Global styles and utilities
├── components.css           # Component-specific styles
└── tailwind.config.ts       # Tailwind configuration
```

### Step 2: Global Styles Setup

```css
/* app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

/* CSS Variables for theming */
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    --secondary: 210 40% 96%;
    --muted: 210 40% 96%;
    --accent: 210 40% 96%;
    --destructive: 0 84.2% 60.2%;
    --border: 214.3 31.8% 91.4%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --primary: 217.2 91.2% 59.8%;
    /* ... dark theme colors */
  }
}

/* Apply base styles */
@layer base {
  * {
    @apply border-border;
  }
  
  body {
    @apply bg-background text-foreground;
  }
}
```

### Step 3: Component Styling Workflow

#### Method 1: Using Tailwind Classes
```typescript
// Direct Tailwind classes
export function Button({ children, variant = 'primary' }: ButtonProps) {
  return (
    <button className={cn(
      'inline-flex items-center justify-center rounded-md text-sm font-medium',
      'transition-colors focus-visible:outline-none focus-visible:ring-2',
      'disabled:pointer-events-none disabled:opacity-50',
      {
        'bg-primary text-primary-foreground hover:bg-primary/90': variant === 'primary',
        'bg-secondary text-secondary-foreground hover:bg-secondary/80': variant === 'secondary',
        'border border-input bg-background hover:bg-accent': variant === 'outline',
      },
      'h-10 px-4 py-2'
    )}>
      {children}
    </button>
  );
}
```

#### Method 2: Using CSS Classes
```css
/* globals.css */
@layer components {
  .btn {
    @apply inline-flex items-center justify-center rounded-md text-sm font-medium
           transition-colors focus-visible:outline-none focus-visible:ring-2
           disabled:pointer-events-none disabled:opacity-50 h-10 px-4 py-2;
  }
  
  .btn-primary {
    @apply btn bg-primary text-primary-foreground hover:bg-primary/90;
  }
  
  .btn-secondary {
    @apply btn bg-secondary text-secondary-foreground hover:bg-secondary/80;
  }
}
```

```typescript
// Using CSS classes
export function Button({ children, variant = 'primary' }: ButtonProps) {
  return (
    <button className={cn(
      'btn',
      `btn-${variant}`
    )}>
      {children}
    </button>
  );
}
```

### Step 4: Responsive Design

```typescript
// Mobile-first responsive design
export function ResponsiveGrid({ children }: { children: React.ReactNode }) {
  return (
    <div className={cn(
      'grid gap-4',
      'grid-cols-1',          // Mobile: 1 column
      'sm:grid-cols-2',       // Small screens: 2 columns
      'md:grid-cols-3',       // Medium screens: 3 columns
      'lg:grid-cols-4',       // Large screens: 4 columns
      'xl:grid-cols-6'        // Extra large: 6 columns
    )}>
      {children}
    </div>
  );
}
```

### Step 5: Dark Mode Support

```typescript
// components/theme-toggle.tsx
'use client';

import { useTheme } from 'next-themes';
import { Button } from '@/components/ui/button';
import { Moon, Sun } from 'lucide-react';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
    >
      <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
      <span className="sr-only">Toggle theme</span>
    </Button>
  );
}
```

---

## State Management Deep Dive

### Understanding Zustand Stores

Zustand is our state management solution. Here's how it works:

### Step 1: Creating a Store

```typescript
// lib/stores/counter-store.ts
import { create } from 'zustand';
import { persist, devtools } from 'zustand/middleware';

// Define the state interface
interface CounterState {
  count: number;
  increment: () => void;
  decrement: () => void;
  reset: () => void;
  incrementBy: (amount: number) => void;
}

// Create the store
export const useCounterStore = create<CounterState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        count: 0,
        
        // Actions
        increment: () => set((state) => ({ count: state.count + 1 })),
        decrement: () => set((state) => ({ count: state.count - 1 })),
        reset: () => set({ count: 0 }),
        incrementBy: (amount: number) => set((state) => ({ count: state.count + amount })),
      }),
      {
        name: 'counter-store', // localStorage key
        partialize: (state) => ({ count: state.count }), // Only persist count
      }
    ),
    { name: 'Counter Store' } // DevTools name
  )
);
```

### Step 2: Using the Store in Components

```typescript
// components/counter.tsx
'use client';

import { useCounterStore } from '@/lib/stores/counter-store';
import { Button } from '@/components/ui/button';

export function Counter() {
  // Get state and actions from the store
  const { count, increment, decrement, reset, incrementBy } = useCounterStore();
  
  return (
    <div className="flex flex-col items-center gap-4 p-6 trading-card">
      <h2 className="text-2xl font-bold">Counter: {count}</h2>
      
      <div className="flex gap-2">
        <Button onClick={decrement}>-</Button>
        <Button onClick={increment}>+</Button>
        <Button onClick={() => incrementBy(5)}>+5</Button>
        <Button onClick={reset} variant="outline">Reset</Button>
      </div>
    </div>
  );
}
```

### Step 3: Advanced Store with Async Actions

```typescript
// lib/stores/user-store.ts
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

interface User {
  id: string;
  name: string;
  email: string;
}

interface UserState {
  user: User | null;
  users: User[];
  isLoading: boolean;
  error: string | null;
  
  // Actions
  fetchUser: (id: string) => Promise<void>;
  fetchUsers: () => Promise<void>;
  updateUser: (id: string, updates: Partial<User>) => Promise<void>;
  clearError: () => void;
}

export const useUserStore = create<UserState>()(
  devtools(
    (set, get) => ({
      // Initial state
      user: null,
      users: [],
      isLoading: false,
      error: null,
      
      // Async action to fetch a user
      fetchUser: async (id: string) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await fetch(`/api/users/${id}`);
          if (!response.ok) throw new Error('Failed to fetch user');
          
          const user = await response.json();
          set({ user, isLoading: false });
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Unknown error',
            isLoading: false 
          });
        }
      },
      
      // Async action to fetch all users
      fetchUsers: async () => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await fetch('/api/users');
          if (!response.ok) throw new Error('Failed to fetch users');
          
          const users = await response.json();
          set({ users, isLoading: false });
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Unknown error',
            isLoading: false 
          });
        }
      },
      
      // Async action to update a user
      updateUser: async (id: string, updates: Partial<User>) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await fetch(`/api/users/${id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates),
          });
          
          if (!response.ok) throw new Error('Failed to update user');
          
          const updatedUser = await response.json();
          
          // Update the user in the state
          set((state) => ({
            user: state.user?.id === id ? updatedUser : state.user,
            users: state.users.map(user => 
              user.id === id ? updatedUser : user
            ),
            isLoading: false,
          }));
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Unknown error',
            isLoading: false 
          });
        }
      },
      
      clearError: () => set({ error: null }),
    }),
    { name: 'User Store' }
  )
);
```

### Step 4: Using Advanced Store

```typescript
// components/user-profile.tsx
'use client';

import { useEffect } from 'react';
import { useUserStore } from '@/lib/stores/user-store';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Props {
  userId: string;
}

export function UserProfile({ userId }: Props) {
  const { 
    user, 
    isLoading, 
    error, 
    fetchUser, 
    updateUser, 
    clearError 
  } = useUserStore();
  
  // Fetch user on component mount
  useEffect(() => {
    fetchUser(userId);
  }, [userId, fetchUser]);
  
  // Handle user update
  const handleUpdateUser = async () => {
    await updateUser(userId, { name: 'Updated Name' });
  };
  
  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center p-6">
          <div className="loading-spinner w-6 h-6"></div>
        </CardContent>
      </Card>
    );
  }
  
  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-destructive mb-4">Error: {error}</div>
          <Button onClick={clearError}>Clear Error</Button>
        </CardContent>
      </Card>
    );
  }
  
  if (!user) {
    return (
      <Card>
        <CardContent className="p-6">
          <div>User not found</div>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>{user.name}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground mb-4">{user.email}</p>
        <Button onClick={handleUpdateUser}>Update User</Button>
      </CardContent>
    </Card>
  );
}
```

### Step 5: Store Selectors and Computed Values

```typescript
// lib/stores/trading-store.ts (extended)
import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';

// ... existing interfaces

export const useTradingStore = create<TradingStore>()(
  subscribeWithSelector((set, get) => ({
    // ... existing state and actions
  }))
);

// Create selector hooks for computed values
export const useTradingSelectors = () => {
  const store = useTradingStore();
  
  return {
    // Portfolio selectors
    totalPortfolioValue: store.portfolio?.totalValue || 0,
    portfolioChange: store.portfolio?.dailyPnL || 0,
    portfolioChangePercent: store.portfolio
      ? (store.portfolio.dailyPnL / (store.portfolio.totalValue - store.portfolio.dailyPnL)) * 100
      : 0,
    
    // Strategy selectors
    activeStrategies: store.strategies.filter(s => s.status === 'ACTIVE'),
    pausedStrategies: store.strategies.filter(s => s.status === 'PAUSED'),
    stoppedStrategies: store.strategies.filter(s => s.status === 'STOPPED'),
    totalStrategiesReturn: store.strategies.reduce((sum, s) => sum + s.totalReturn, 0) / store.strategies.length || 0,
    
    // Market data selectors
    watchlistData: store.watchlist.map(symbol => store.marketData[symbol]).filter(Boolean),
    selectedSymbolData: store.selectedSymbol ? store.marketData[store.selectedSymbol] : null,
  };
};

// Usage in components
export function PortfolioDashboard() {
  const { 
    totalPortfolioValue, 
    portfolioChange, 
    portfolioChangePercent,
    activeStrategies 
  } = useTradingSelectors();
  
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardContent className="p-6">
          <div className="text-sm text-muted-foreground">Total Value</div>
          <div className="text-2xl font-bold">${totalPortfolioValue.toLocaleString()}</div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-6">
          <div className="text-sm text-muted-foreground">Daily P&L</div>
          <div className={`text-2xl font-bold ${
            portfolioChange >= 0 ? 'profit-text' : 'loss-text'
          }`}>
            {portfolioChange >= 0 ? '+' : ''}${portfolioChange.toFixed(2)}
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-6">
          <div className="text-sm text-muted-foreground">Active Strategies</div>
          <div className="text-2xl font-bold">{activeStrategies.length}</div>
        </CardContent>
      </Card>
    </div>
  );
}
```

---

## Authentication Implementation

### Understanding the Auth System

Our authentication system consists of:
1. **JWT Tokens** - Stored in localStorage
2. **Auth Context** - React context for auth state
3. **Auth Store** - Zustand store for persistence
4. **Protected Routes** - Route protection components
5. **Auth Forms** - Login/register components

### Step 1: Auth Types and Utilities

```typescript
// lib/types/auth.ts
export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: 'USER' | 'ADMIN' | 'PREMIUM';
  isVerified: boolean;
  twoFactorEnabled: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
}

export interface AuthResponse {
  user: User;
  token: string;
  refreshToken: string;
}
```

### Step 2: Auth API Functions

```typescript
// lib/api/auth.ts
import { LoginCredentials, RegisterCredentials, AuthResponse } from '@/lib/types/auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

export class AuthAPI {
  static async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Login failed');
    }
    
    return response.json();
  }
  
  static async register(credentials: RegisterCredentials): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Registration failed');
    }
    
    return response.json();
  }
  
  static async refreshToken(refreshToken: string): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refreshToken }),
    });
    
    if (!response.ok) {
      throw new Error('Token refresh failed');
    }
    
    return response.json();
  }
  
  static async logout(): Promise<void> {
    const token = localStorage.getItem('alphintra_auth_token');
    
    if (token) {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
    }
  }
}
```

### Step 3: Login Form Component

```typescript
// components/auth/login-form.tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/components/auth/auth-provider';
import { AuthAPI } from '@/lib/api/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from '@/components/ui/toaster';
import { Eye, EyeOff, Mail, Lock } from 'lucide-react';

export function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email || !password) {
      toast.error('Please fill in all fields');
      return;
    }
    
    setIsLoading(true);
    
    try {
      const response = await AuthAPI.login({ email, password });
      login(response.token, response.user);
      toast.success('Login successful!');
      router.push('/dashboard');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl">Welcome Back</CardTitle>
        <CardDescription>
          Sign in to your Alphintra account
        </CardDescription>
      </CardHeader>
      
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <div className="relative">
              <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                id="email"
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="pl-10"
                required
              />
            </div>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pl-10 pr-10"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-3 text-muted-foreground hover:text-foreground"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>
          
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? 'Signing in...' : 'Sign In'}
          </Button>
        </form>
        
        <div className="mt-4 text-center text-sm">
          <a href="/forgot-password" className="text-primary hover:underline">
            Forgot your password?
          </a>
        </div>
        
        <div className="mt-6 text-center text-sm">
          Don't have an account?{' '}
          <a href="/register" className="text-primary hover:underline">
            Sign up
          </a>
        </div>
      </CardContent>
    </Card>
  );
}
```

### Step 4: Protected Route Component

```typescript
// components/auth/protected-route.tsx
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/components/auth/auth-provider';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: 'USER' | 'ADMIN' | 'PREMIUM';
  redirectTo?: string;
}

export function ProtectedRoute({ 
  children, 
  requiredRole = 'USER',
  redirectTo = '/login' 
}: ProtectedRouteProps) {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  
  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        router.push(redirectTo);
        return;
      }
      
      if (requiredRole && user) {
        const roleHierarchy = { 'USER': 1, 'PREMIUM': 2, 'ADMIN': 3 };
        if (roleHierarchy[user.role] < roleHierarchy[requiredRole]) {
          router.push('/unauthorized');
          return;
        }
      }
    }
  }, [isAuthenticated, isLoading, user, requiredRole, redirectTo, router]);
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="loading-spinner w-8 h-8"></div>
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return null; // Will redirect
  }
  
  if (requiredRole && user) {
    const roleHierarchy = { 'USER': 1, 'PREMIUM': 2, 'ADMIN': 3 };
    if (roleHierarchy[user.role] < roleHierarchy[requiredRole]) {
      return null; // Will redirect
    }
  }
  
  return <>{children}</>;
}
```

### Step 5: Using Authentication in Pages

```typescript
// app/(dashboard)/dashboard/page.tsx
import { Metadata } from 'next';
import { DashboardContent } from '@/components/dashboard/dashboard-content';

export const metadata: Metadata = {
  title: 'Dashboard',
  description: 'Your trading dashboard',
};

export default function DashboardPage() {
  // Protection is handled by the layout
  return <DashboardContent />;
}

// app/(dashboard)/layout.tsx
import { ProtectedRoute } from '@/components/auth/protected-route';
import { DashboardSidebar } from '@/components/layout/dashboard-sidebar';
import { DashboardHeader } from '@/components/layout/dashboard-header';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute>
      <div className="flex h-screen bg-background">
        <DashboardSidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <DashboardHeader />
          <main className="flex-1 overflow-auto p-6">
            {children}
          </main>
        </div>
      </div>
    </ProtectedRoute>
  );
}
```

---

## GraphQL Integration Step-by-Step

### Step 1: Understanding Our GraphQL Setup

Our GraphQL integration uses Apollo Client with:
- HTTP Link for queries and mutations
- WebSocket Link for real-time subscriptions
- Authentication handling
- Error handling and token refresh

### Step 2: Writing GraphQL Queries

```typescript
// lib/graphql/queries.ts
import { gql } from '@apollo/client';

export const GET_USER_PROFILE = gql`
  query GetUserProfile {
    me {
      id
      email
      firstName
      lastName
      role
      isVerified
      twoFactorEnabled
      createdAt
      updatedAt
    }
  }
`;

export const GET_PORTFOLIO = gql`
  query GetPortfolio {
    portfolio {
      id
      totalValue
      cashBalance
      dailyPnL
      totalPnL
      positions {
        id
        symbol
        quantity
        averagePrice
        currentPrice
        unrealizedPnL
        realizedPnL
        side
      }
    }
  }
`;

export const GET_STRATEGIES = gql`
  query GetStrategies($filter: StrategyFilter, $sort: StrategySort) {
    strategies(filter: $filter, sort: $sort) {
      edges {
        node {
          id
          name
          description
          status
          totalReturn
          sharpeRatio
          maxDrawdown
          winRate
          totalTrades
          createdAt
          updatedAt
        }
      }
      pageInfo {
        hasNextPage
        hasPreviousPage
        startCursor
        endCursor
      }
    }
  }
`;

export const GET_MARKET_DATA = gql`
  query GetMarketData($symbols: [String!]!, $timeframe: String!) {
    marketData(symbols: $symbols, timeframe: $timeframe) {
      symbol
      price
      change
      changePercent
      volume
      high24h
      low24h
      timestamp
      candles {
        timestamp
        open
        high
        low
        close
        volume
      }
    }
  }
`;
```

### Step 3: Writing GraphQL Mutations

```typescript
// lib/graphql/mutations.ts
import { gql } from '@apollo/client';

export const CREATE_STRATEGY = gql`
  mutation CreateStrategy($input: CreateStrategyInput!) {
    createStrategy(input: $input) {
      id
      name
      description
      status
      createdAt
    }
  }
`;

export const UPDATE_STRATEGY = gql`
  mutation UpdateStrategy($id: ID!, $input: UpdateStrategyInput!) {
    updateStrategy(id: $id, input: $input) {
      id
      name
      description
      status
      totalReturn
      sharpeRatio
      maxDrawdown
      updatedAt
    }
  }
`;

export const DELETE_STRATEGY = gql`
  mutation DeleteStrategy($id: ID!) {
    deleteStrategy(id: $id) {
      success
      message
    }
  }
`;

export const EXECUTE_TRADE = gql`
  mutation ExecuteTrade($input: ExecuteTradeInput!) {
    executeTrade(input: $input) {
      id
      symbol
      side
      quantity
      price
      status
      timestamp
    }
  }
`;
```

### Step 4: Writing GraphQL Subscriptions

```typescript
// lib/graphql/subscriptions.ts
import { gql } from '@apollo/client';

export const MARKET_DATA_SUBSCRIPTION = gql`
  subscription MarketDataUpdates($symbols: [String!]!) {
    marketDataUpdates(symbols: $symbols) {
      symbol
      price
      change
      changePercent
      volume
      timestamp
    }
  }
`;

export const PORTFOLIO_UPDATES = gql`
  subscription PortfolioUpdates {
    portfolioUpdates {
      totalValue
      cashBalance
      dailyPnL
      totalPnL
      positions {
        id
        symbol
        quantity
        currentPrice
        unrealizedPnL
      }
    }
  }
`;

export const STRATEGY_UPDATES = gql`
  subscription StrategyUpdates($strategyId: ID!) {
    strategyUpdates(strategyId: $strategyId) {
      id
      status
      totalReturn
      sharpeRatio
      maxDrawdown
      lastTrade {
        id
        symbol
        side
        quantity
        price
        timestamp
      }
    }
  }
`;
```

### Step 5: Creating Custom Hooks

```typescript
// hooks/use-portfolio.ts
import { useQuery, useSubscription } from '@apollo/client';
import { GET_PORTFOLIO, PORTFOLIO_UPDATES } from '@/lib/graphql/queries';

export function usePortfolio() {
  // Query for initial data
  const { data, loading, error, refetch } = useQuery(GET_PORTFOLIO, {
    errorPolicy: 'all',
    notifyOnNetworkStatusChange: true,
  });
  
  // Subscribe to real-time updates
  const { data: subscriptionData } = useSubscription(PORTFOLIO_UPDATES, {
    onData: ({ data }) => {
      console.log('Portfolio updated:', data.data);
    },
  });
  
  // Use subscription data if available, otherwise use query data
  const portfolio = subscriptionData?.portfolioUpdates || data?.portfolio;
  
  return {
    portfolio,
    loading,
    error,
    refetch,
  };
}
```

```typescript
// hooks/use-strategies.ts
import { useQuery, useMutation } from '@apollo/client';
import { GET_STRATEGIES, CREATE_STRATEGY, UPDATE_STRATEGY, DELETE_STRATEGY } from '@/lib/graphql/queries';
import { toast } from '@/components/ui/toaster';

export function useStrategies(filter?: any, sort?: any) {
  // Query strategies
  const { data, loading, error, refetch, fetchMore } = useQuery(GET_STRATEGIES, {
    variables: { filter, sort },
    errorPolicy: 'all',
  });
  
  // Create strategy mutation
  const [createStrategyMutation, { loading: creating }] = useMutation(CREATE_STRATEGY, {
    refetchQueries: [{ query: GET_STRATEGIES, variables: { filter, sort } }],
    onCompleted: () => {
      toast.success('Strategy created successfully');
    },
    onError: (error) => {
      toast.error(`Failed to create strategy: ${error.message}`);
    },
  });
  
  // Update strategy mutation
  const [updateStrategyMutation, { loading: updating }] = useMutation(UPDATE_STRATEGY, {
    onCompleted: () => {
      toast.success('Strategy updated successfully');
    },
    onError: (error) => {
      toast.error(`Failed to update strategy: ${error.message}`);
    },
  });
  
  // Delete strategy mutation
  const [deleteStrategyMutation, { loading: deleting }] = useMutation(DELETE_STRATEGY, {
    refetchQueries: [{ query: GET_STRATEGIES, variables: { filter, sort } }],
    onCompleted: () => {
      toast.success('Strategy deleted successfully');
    },
    onError: (error) => {
      toast.error(`Failed to delete strategy: ${error.message}`);
    },
  });
  
  const strategies = data?.strategies?.edges?.map(edge => edge.node) || [];
  const pageInfo = data?.strategies?.pageInfo;
  
  const createStrategy = async (input: any) => {
    try {
      const result = await createStrategyMutation({ variables: { input } });
      return result.data?.createStrategy;
    } catch (error) {
      throw error;
    }
  };
  
  const updateStrategy = async (id: string, input: any) => {
    try {
      const result = await updateStrategyMutation({ variables: { id, input } });
      return result.data?.updateStrategy;
    } catch (error) {
      throw error;
    }
  };
  
  const deleteStrategy = async (id: string) => {
    try {
      const result = await deleteStrategyMutation({ variables: { id } });
      return result.data?.deleteStrategy;
    } catch (error) {
      throw error;
    }
  };
  
  const loadMore = () => {
    if (pageInfo?.hasNextPage) {
      fetchMore({
        variables: {
          cursor: pageInfo.endCursor,
        },
        updateQuery: (prev, { fetchMoreResult }) => {
          if (!fetchMoreResult) return prev;
          
          return {
            strategies: {
              ...fetchMoreResult.strategies,
              edges: [
                ...prev.strategies.edges,
                ...fetchMoreResult.strategies.edges,
              ],
            },
          };
        },
      });
    }
  };
  
  return {
    strategies,
    loading,
    error,
    creating,
    updating,
    deleting,
    pageInfo,
    refetch,
    loadMore,
    createStrategy,
    updateStrategy,
    deleteStrategy,
  };
}
```

### Step 6: Using GraphQL in Components

```typescript
// components/trading/strategy-list.tsx
'use client';

import { useState } from 'react';
import { useStrategies } from '@/hooks/use-strategies';
import { StrategyCard } from '@/components/trading/strategy-card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Search } from 'lucide-react';

export function StrategyList() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [sortBy, setSortBy] = useState('CREATED_AT_DESC');
  
  // Build filter object
  const filter = {
    ...(searchTerm && { search: searchTerm }),
    ...(statusFilter !== 'ALL' && { status: statusFilter }),
  };
  
  const sort = sortBy;
  
  const {
    strategies,
    loading,
    error,
    creating,
    pageInfo,
    loadMore,
    createStrategy,
    updateStrategy,
    deleteStrategy,
  } = useStrategies(filter, sort);
  
  const handleCreateStrategy = async () => {
    try {
      await createStrategy({
        name: 'New Strategy',
        description: 'A new trading strategy',
        type: 'MANUAL',
      });
    } catch (error) {
      console.error('Failed to create strategy:', error);
    }
  };
  
  const handleStatusChange = async (id: string, status: string) => {
    try {
      await updateStrategy(id, { status });
    } catch (error) {
      console.error('Failed to update strategy:', error);
    }
  };
  
  const handleDeleteStrategy = async (id: string) => {
    if (confirm('Are you sure you want to delete this strategy?')) {
      try {
        await deleteStrategy(id);
      } catch (error) {
        console.error('Failed to delete strategy:', error);
      }
    }
  };
  
  if (loading && strategies.length === 0) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="loading-spinner w-8 h-8"></div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="text-center p-8">
        <div className="text-destructive mb-4">
          Error loading strategies: {error.message}
        </div>
        <Button onClick={() => window.location.reload()}>
          Retry
        </Button>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Strategies</h1>
        <Button onClick={handleCreateStrategy} disabled={creating}>
          <Plus className="w-4 h-4 mr-2" />
          {creating ? 'Creating...' : 'Create Strategy'}
        </Button>
      </div>
      
      {/* Filters */}
      <div className="flex gap-4 flex-wrap">
        <div className="flex-1 min-w-[200px]">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search strategies..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All Statuses</SelectItem>
            <SelectItem value="ACTIVE">Active</SelectItem>
            <SelectItem value="PAUSED">Paused</SelectItem>
            <SelectItem value="STOPPED">Stopped</SelectItem>
          </SelectContent>
        </Select>
        
        <Select value={sortBy} onValueChange={setSortBy}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Sort by" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="CREATED_AT_DESC">Newest First</SelectItem>
            <SelectItem value="CREATED_AT_ASC">Oldest First</SelectItem>
            <SelectItem value="TOTAL_RETURN_DESC">Best Performance</SelectItem>
            <SelectItem value="TOTAL_RETURN_ASC">Worst Performance</SelectItem>
            <SelectItem value="NAME_ASC">Name A-Z</SelectItem>
            <SelectItem value="NAME_DESC">Name Z-A</SelectItem>
          </SelectContent>
        </Select>
      </div>
      
      {/* Strategy Grid */}
      {strategies.length === 0 ? (
        <div className="text-center p-8">
          <div className="text-muted-foreground mb-4">
            No strategies found
          </div>
          <Button onClick={handleCreateStrategy} disabled={creating}>
            <Plus className="w-4 h-4 mr-2" />
            Create Your First Strategy
          </Button>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {strategies.map((strategy) => (
            <StrategyCard
              key={strategy.id}
              strategy={strategy}
              onStatusChange={handleStatusChange}
              onDelete={handleDeleteStrategy}
            />
          ))}
        </div>
      )}
      
      {/* Load More */}
      {pageInfo?.hasNextPage && (
        <div className="text-center">
          <Button variant="outline" onClick={loadMore} disabled={loading}>
            {loading ? 'Loading...' : 'Load More'}
          </Button>
        </div>
      )}
    </div>
  );
}
```

---

## How Every Code File Works

### Understanding the Application Flow

Let's trace through how the application works from startup to user interaction:

### 1. Application Startup

**File: `app/layout.tsx`**
```typescript
// This is the FIRST component that renders
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="min-h-screen bg-background font-sans antialiased">
        <Providers>  {/* This wraps the entire app */}
          {children}  {/* This is where pages render */}
          <Toaster />  {/* Global toast notifications */}
        </Providers>
      </body>
    </html>
  );
}
```

**What happens here:**
1. HTML structure is set up
2. Font variables are applied
3. Global CSS classes are applied
4. `<Providers>` wraps everything to provide global context
5. `{children}` is where the actual page content renders
6. `<Toaster />` provides global notifications

**File: `components/providers.tsx`**
```typescript
export function Providers({ children }: ProvidersProps) {
  return (
    <ThemeProvider>          // Handles light/dark theme
      <ApolloProvider>       // Provides GraphQL client
        <AuthProvider>       // Provides authentication state
          {children}
        </AuthProvider>
      </ApolloProvider>
    </ThemeProvider>
  );
}
```

**What happens here:**
1. Theme system is initialized
2. Apollo GraphQL client is made available
3. Authentication system is initialized
4. All child components can now access these contexts

### 2. Page Rendering

**File: `app/page.tsx` (Home page)**
```typescript
export default function HomePage() {
  return <LandingPage />;  // Renders the landing page component
}
```

**What happens here:**
1. Next.js renders this when user visits `/`
2. It simply renders the `LandingPage` component
3. This is a simple page that doesn't need authentication

**File: `components/landing/landing-page.tsx`**
```typescript
export function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-secondary/20">
      {/* Header with navigation */}
      <header>...</header>
      
      {/* Hero section */}
      <section>...</section>
      
      {/* Features section */}
      <section>...</section>
      
      {/* Footer */}
      <footer>...</footer>
    </div>
  );
}
```

**What happens here:**
1. Full landing page is rendered with all sections
2. Navigation links allow users to go to login/register
3. Responsive design adapts to different screen sizes

### 3. Authentication Flow

**User clicks "Sign In" button:**

**File: `app/(auth)/login/page.tsx`**
```typescript
export default function LoginPage() {
  return <LoginForm />;  // Renders the login form
}
```

**File: `components/auth/login-form.tsx`**
```typescript
export function LoginForm() {
  const { login } = useAuth();  // Get login function from auth context
  
  const handleSubmit = async (e: React.FormEvent) => {
    // 1. Prevent default form submission
    e.preventDefault();
    
    // 2. Call API to authenticate
    const response = await AuthAPI.login({ email, password });
    
    // 3. If successful, update auth state
    login(response.token, response.user);
    
    // 4. Redirect to dashboard
    router.push('/dashboard');
  };
  
  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
    </form>
  );
}
```

**What happens here:**
1. User enters email/password
2. Form submission calls API
3. If successful, auth state is updated
4. User is redirected to dashboard

### 4. Protected Route Access

**User tries to access `/dashboard`:**

**File: `app/(dashboard)/layout.tsx`**
```typescript
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>  {/* This checks authentication */}
      <div className="flex h-screen">
        <Sidebar />
        <div className="flex-1">
          <Header />
          <main>{children}</main>  {/* Dashboard pages render here */}
        </div>
      </div>
    </ProtectedRoute>
  );
}
```

**File: `components/auth/protected-route.tsx`**
```typescript
export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();
  
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');  // Redirect if not authenticated
    }
  }, [isAuthenticated, isLoading]);
  
  if (isLoading) return <LoadingSpinner />;
  if (!isAuthenticated) return null;  // Will redirect
  
  return <>{children}</>;  // Render children if authenticated
}
```

**What happens here:**
1. `ProtectedRoute` checks if user is authenticated
2. If not authenticated, user is redirected to login
3. If authenticated, dashboard layout is rendered
4. Dashboard page content renders inside the layout

### 5. Dashboard Page Rendering

**File: `app/(dashboard)/dashboard/page.tsx`**
```typescript
export default function DashboardPage() {
  return <DashboardContent />;
}
```

**File: `components/dashboard/dashboard-content.tsx`**
```typescript
export function DashboardContent() {
  const { portfolio } = usePortfolio();  // Fetch portfolio data
  const { strategies } = useStrategies();  // Fetch strategies data
  
  return (
    <div className="space-y-6">
      <h1>Dashboard</h1>
      <PortfolioSummary portfolio={portfolio} />
      <StrategyGrid strategies={strategies} />
    </div>
  );
}
```

**What happens here:**
1. Component uses custom hooks to fetch data
2. Hooks use GraphQL queries to get data from API
3. Data is displayed in UI components
4. Real-time subscriptions update data automatically

### 6. Data Fetching with GraphQL

**File: `hooks/use-portfolio.ts`**
```typescript
export function usePortfolio() {
  // Query for initial data
  const { data, loading, error } = useQuery(GET_PORTFOLIO);
  
  // Subscribe to real-time updates
  useSubscription(PORTFOLIO_UPDATES, {
    onData: ({ data }) => {
      // Update UI when data changes
    },
  });
  
  return { portfolio: data?.portfolio, loading, error };
}
```

**What happens here:**
1. `useQuery` fetches initial portfolio data
2. `useSubscription` listens for real-time updates
3. Component re-renders when data changes
4. Loading and error states are handled

### 7. State Management Flow

**File: `lib/stores/trading-store.ts`**
```typescript
export const useTradingStore = create<TradingStore>((set, get) => ({
  portfolio: null,
  strategies: [],
  
  setPortfolio: (portfolio) => set({ portfolio }),
  addStrategy: (strategy) => set((state) => ({
    strategies: [...state.strategies, strategy]
  })),
}));
```

**Usage in components:**
```typescript
export function SomeComponent() {
  const { portfolio, setPortfolio } = useTradingStore();
  
  // When portfolio data is fetched
  useEffect(() => {
    if (portfolioData) {
      setPortfolio(portfolioData);  // Update global state
    }
  }, [portfolioData, setPortfolio]);
}
```

**What happens here:**
1. Zustand store holds global state
2. Components can read and update state
3. State changes trigger re-renders
4. State persists across page navigation

### 8. Styling and Theming

**File: `app/globals.css`**
```css
/* CSS variables for theming */
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 221.2 83.2% 53.3%;
}

.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  --primary: 217.2 91.2% 59.8%;
}

/* Utility classes */
.trading-card {
  @apply bg-card border border-border rounded-lg shadow-sm p-4;
}
```

**Usage in components:**
```typescript
export function Card({ children }: CardProps) {
  return (
    <div className="trading-card">  {/* Uses custom CSS class */}
      {children}
    </div>
  );
}
```

**What happens here:**
1. CSS variables define theme colors
2. Tailwind uses these variables for consistent theming
3. Custom utility classes provide reusable styling
4. Components apply classes for consistent design

### 9. Error Handling

**File: `app/error.tsx`**
```typescript
'use client';

export default function Error({ error, reset }: ErrorProps) {
  return (
    <div className="error-container">
      <h2>Something went wrong!</h2>
      <button onClick={reset}>Try again</button>
    </div>
  );
}
```

**What happens here:**
1. Next.js renders this when an error occurs
2. User can retry the failed operation
3. Error boundary prevents app crash

### 10. Complete Request Flow

**Example: User creates a new strategy**

1. **User interaction:** Clicks "Create Strategy" button
2. **Component:** `StrategyList` component handles click
3. **Hook:** Calls `createStrategy` from `useStrategies` hook
4. **GraphQL:** Hook executes `CREATE_STRATEGY` mutation
5. **Apollo:** Sends GraphQL request to backend API
6. **API:** Backend processes request and returns response
7. **Apollo:** Receives response and updates cache
8. **Hook:** Triggers refetch of strategies list
9. **Component:** Re-renders with updated data
10. **Store:** Global state is updated if needed
11. **UI:** User sees new strategy in the list
12. **Toast:** Success notification is shown

This is the complete flow from user interaction to UI update!

---

## Development Workflow

### Daily Development Process

#### 1. Starting Development

```bash
# 1. Start the development server
npm run dev

# 2. Open in browser
# http://localhost:3000 (or 3001, 3002 if ports are taken)

# 3. Open your code editor
code .
```

#### 2. Making Changes

**Adding a new feature:**

```bash
# 1. Create feature branch (if using git)
git checkout -b feature/new-dashboard-widget

# 2. Plan your changes
# - What components do you need?
# - What pages will be affected?
# - What data do you need to fetch?
# - What state management is required?
```

**Example: Adding a new widget to dashboard**

```typescript
// Step 1: Create the component
// components/dashboard/profit-loss-widget.tsx
export function ProfitLossWidget() {
  const { portfolio } = usePortfolio();
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Today's P&L</CardTitle>
      </CardHeader>
      <CardContent>
        <div className={cn(
          'text-2xl font-bold',
          portfolio?.dailyPnL >= 0 ? 'profit-text' : 'loss-text'
        )}>
          {portfolio?.dailyPnL >= 0 ? '+' : ''}
          ${portfolio?.dailyPnL?.toFixed(2) || '0.00'}
        </div>
      </CardContent>
    </Card>
  );
}

// Step 2: Add to dashboard
// components/dashboard/dashboard-content.tsx
import { ProfitLossWidget } from './profit-loss-widget';

export function DashboardContent() {
  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
      <ProfitLossWidget />  {/* Add the new widget */}
      {/* Other widgets */}
    </div>
  );
}
```

#### 3. Testing Changes

```bash
# 1. Check for TypeScript errors
npm run type-check

# 2. Check for linting issues
npm run lint

# 3. Build to ensure everything compiles
npm run build

# 4. Test in browser
# - Navigate to different pages
# - Test responsive design
# - Check console for errors
```

#### 4. Debugging

**Common debugging techniques:**

```typescript
// 1. Console logging
export function MyComponent() {
  const { data, loading, error } = useQuery(GET_DATA);
  
  console.log('Component render:', { data, loading, error });
  
  useEffect(() => {
    console.log('Data changed:', data);
  }, [data]);
}

// 2. React DevTools
// Install React DevTools browser extension
// Inspect component state and props

// 3. Apollo DevTools
// Install Apollo Client DevTools
// View GraphQL queries and cache

// 4. Zustand DevTools
// View state changes in Redux DevTools
```

### Project Organization Best Practices

#### 1. File Naming Conventions

```
components/
├── ui/
│   ├── button.tsx           # Component name in kebab-case
│   ├── input.tsx
│   └── modal.tsx
├── trading/
│   ├── strategy-card.tsx    # Descriptive, specific names
│   ├── portfolio-summary.tsx
│   └── market-data-widget.tsx
└── auth/
    ├── login-form.tsx       # Form components end with -form
    ├── register-form.tsx
    └── auth-provider.tsx    # Context providers end with -provider
```

#### 2. Component Structure Pattern

```typescript
// components/example/example-component.tsx

// 1. Imports (external first, then internal)
import React, { useState, useEffect } from 'react';
import { useQuery } from '@apollo/client';
import { Button } from '@/components/ui/button';
import { useExampleStore } from '@/lib/stores/example-store';

// 2. Type definitions
interface ExampleComponentProps {
  title: string;
  onAction?: () => void;
}

// 3. Component definition
export function ExampleComponent({ title, onAction }: ExampleComponentProps) {
  // 4. Hooks (state, effects, custom hooks)
  const [isVisible, setIsVisible] = useState(false);
  const { data, loading } = useQuery(GET_EXAMPLE_DATA);
  
  // 5. Event handlers
  const handleClick = () => {
    setIsVisible(!isVisible);
    onAction?.();
  };
  
  // 6. Effects
  useEffect(() => {
    // Side effects
  }, []);
  
  // 7. Early returns (loading, error states)
  if (loading) return <div>Loading...</div>;
  
  // 8. Main render
  return (
    <div className="example-component">
      <h2>{title}</h2>
      <Button onClick={handleClick}>Toggle</Button>
      {isVisible && <div>Content</div>}
    </div>
  );
}
```

#### 3. Adding New Pages

**Step-by-step process:**

```bash
# 1. Create page directory
mkdir -p app/new-feature

# 2. Create page file
touch app/new-feature/page.tsx

# 3. Create layout if needed
touch app/new-feature/layout.tsx

# 4. Create loading state
touch app/new-feature/loading.tsx

# 5. Create error state
touch app/new-feature/error.tsx
```

```typescript
// app/new-feature/page.tsx
import { Metadata } from 'next';
import { NewFeatureContent } from '@/components/new-feature/new-feature-content';

export const metadata: Metadata = {
  title: 'New Feature - Alphintra',
  description: 'Description of the new feature',
};

export default function NewFeaturePage() {
  return <NewFeatureContent />;
}

// app/new-feature/layout.tsx
import { NewFeatureSidebar } from '@/components/new-feature/sidebar';

export default function NewFeatureLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex">
      <NewFeatureSidebar />
      <main className="flex-1">{children}</main>
    </div>
  );
}

// app/new-feature/loading.tsx
export default function NewFeatureLoading() {
  return (
    <div className="flex items-center justify-center h-screen">
      <div className="loading-spinner w-8 h-8"></div>
    </div>
  );
}
```

### Advanced Development Patterns

#### 1. Higher-Order Components

```typescript
// components/hoc/with-auth.tsx
export function withAuth<P extends {}>(
  Component: React.ComponentType<P>,
  requiredRole: 'USER' | 'ADMIN' | 'PREMIUM' = 'USER'
) {
  return function AuthenticatedComponent(props: P) {
    const { user, isAuthenticated } = useAuth();
    
    if (!isAuthenticated) {
      return <div>Please log in</div>;
    }
    
    if (requiredRole && user && user.role !== requiredRole) {
      return <div>Insufficient permissions</div>;
    }
    
    return <Component {...props} />;
  };
}

// Usage
const AdminPanel = withAuth(AdminPanelComponent, 'ADMIN');
```

#### 2. Compound Components

```typescript
// components/ui/tabs.tsx
interface TabsContextType {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const TabsContext = createContext<TabsContextType | undefined>(undefined);

export function Tabs({ children, defaultTab }: TabsProps) {
  const [activeTab, setActiveTab] = useState(defaultTab);
  
  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div className="tabs">{children}</div>
    </TabsContext.Provider>
  );
}

export function TabsList({ children }: TabsListProps) {
  return <div className="tabs-list">{children}</div>;
}

export function TabsTrigger({ value, children }: TabsTriggerProps) {
  const { activeTab, setActiveTab } = useContext(TabsContext);
  
  return (
    <button
      className={cn('tab-trigger', activeTab === value && 'active')}
      onClick={() => setActiveTab(value)}
    >
      {children}
    </button>
  );
}

export function TabsContent({ value, children }: TabsContentProps) {
  const { activeTab } = useContext(TabsContext);
  
  if (activeTab !== value) return null;
  
  return <div className="tab-content">{children}</div>;
}

// Usage
<Tabs defaultTab="overview">
  <TabsList>
    <TabsTrigger value="overview">Overview</TabsTrigger>
    <TabsTrigger value="analytics">Analytics</TabsTrigger>
  </TabsList>
  <TabsContent value="overview">Overview content</TabsContent>
  <TabsContent value="analytics">Analytics content</TabsContent>
</Tabs>
```

#### 3. Custom Hooks Pattern

```typescript
// hooks/use-local-storage.ts
export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') return initialValue;
    
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });
  
  const setValue = (value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      }
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error);
    }
  };
  
  return [storedValue, setValue] as const;
}

// Usage
export function Settings() {
  const [theme, setTheme] = useLocalStorage('theme', 'light');
  const [language, setLanguage] = useLocalStorage('language', 'en');
  
  return (
    <div>
      <button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
        Toggle Theme
      </button>
    </div>
  );
}
```

---

## Real-World Examples

### Example 1: Complete Feature Implementation

Let's implement a complete "Strategy Performance Analytics" feature:

#### Step 1: Plan the Feature

**Requirements:**
- Show strategy performance metrics
- Display performance charts
- Allow filtering by date range
- Export data functionality

**Files we'll need:**
- `app/strategies/[id]/analytics/page.tsx` - The page
- `components/analytics/performance-chart.tsx` - Chart component
- `components/analytics/metrics-grid.tsx` - Metrics display
- `components/analytics/date-range-picker.tsx` - Date filter
- `hooks/use-strategy-analytics.ts` - Data fetching
- `lib/graphql/analytics-queries.ts` - GraphQL queries

#### Step 2: Create GraphQL Queries

```typescript
// lib/graphql/analytics-queries.ts
import { gql } from '@apollo/client';

export const GET_STRATEGY_ANALYTICS = gql`
  query GetStrategyAnalytics(
    $strategyId: ID!
    $startDate: String!
    $endDate: String!
    $timeframe: String!
  ) {
    strategyAnalytics(
      strategyId: $strategyId
      startDate: $startDate
      endDate: $endDate
      timeframe: $timeframe
    ) {
      totalReturn
      sharpeRatio
      maxDrawdown
      volatility
      winRate
      profitFactor
      totalTrades
      
      performanceData {
        timestamp
        cumulativeReturn
        dailyReturn
        drawdown
      }
      
      monthlyReturns {
        month
        return
      }
      
      tradeDistribution {
        profitTrades
        lossTrades
        avgProfit
        avgLoss
      }
    }
  }
`;
```

#### Step 3: Create Custom Hook

```typescript
// hooks/use-strategy-analytics.ts
import { useQuery } from '@apollo/client';
import { useState } from 'react';
import { GET_STRATEGY_ANALYTICS } from '@/lib/graphql/analytics-queries';

export function useStrategyAnalytics(strategyId: string) {
  const [dateRange, setDateRange] = useState({
    startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(), // 30 days ago
    endDate: new Date().toISOString(),
  });
  
  const [timeframe, setTimeframe] = useState('1d');
  
  const { data, loading, error, refetch } = useQuery(GET_STRATEGY_ANALYTICS, {
    variables: {
      strategyId,
      startDate: dateRange.startDate,
      endDate: dateRange.endDate,
      timeframe,
    },
    skip: !strategyId,
  });
  
  const updateDateRange = (start: string, end: string) => {
    setDateRange({ startDate: start, endDate: end });
  };
  
  const exportData = async () => {
    if (!data?.strategyAnalytics) return;
    
    const csvData = data.strategyAnalytics.performanceData
      .map(row => `${row.timestamp},${row.cumulativeReturn},${row.dailyReturn}`)
      .join('\n');
    
    const blob = new Blob([`Date,Cumulative Return,Daily Return\n${csvData}`], {
      type: 'text/csv',
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `strategy-${strategyId}-analytics.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };
  
  return {
    analytics: data?.strategyAnalytics,
    loading,
    error,
    dateRange,
    timeframe,
    updateDateRange,
    setTimeframe,
    exportData,
    refetch,
  };
}
```

#### Step 4: Create Components

```typescript
// components/analytics/metrics-grid.tsx
interface MetricsGridProps {
  analytics: {
    totalReturn: number;
    sharpeRatio: number;
    maxDrawdown: number;
    volatility: number;
    winRate: number;
    profitFactor: number;
    totalTrades: number;
  };
}

export function MetricsGrid({ analytics }: MetricsGridProps) {
  const metrics = [
    {
      label: 'Total Return',
      value: `${analytics.totalReturn.toFixed(2)}%`,
      className: analytics.totalReturn >= 0 ? 'profit-text' : 'loss-text',
    },
    {
      label: 'Sharpe Ratio',
      value: analytics.sharpeRatio.toFixed(2),
      className: analytics.sharpeRatio >= 1 ? 'profit-text' : 'text-foreground',
    },
    {
      label: 'Max Drawdown',
      value: `${analytics.maxDrawdown.toFixed(2)}%`,
      className: 'loss-text',
    },
    {
      label: 'Volatility',
      value: `${analytics.volatility.toFixed(2)}%`,
      className: 'text-foreground',
    },
    {
      label: 'Win Rate',
      value: `${analytics.winRate.toFixed(1)}%`,
      className: analytics.winRate >= 50 ? 'profit-text' : 'loss-text',
    },
    {
      label: 'Profit Factor',
      value: analytics.profitFactor.toFixed(2),
      className: analytics.profitFactor >= 1 ? 'profit-text' : 'loss-text',
    },
    {
      label: 'Total Trades',
      value: analytics.totalTrades.toString(),
      className: 'text-foreground',
    },
  ];
  
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
      {metrics.map((metric) => (
        <Card key={metric.label}>
          <CardContent className="p-4 text-center">
            <div className="text-sm text-muted-foreground mb-1">
              {metric.label}
            </div>
            <div className={`text-xl font-bold ${metric.className}`}>
              {metric.value}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
```

```typescript
// components/analytics/performance-chart.tsx
'use client';

import { useEffect, useRef } from 'react';
import { createChart, IChartApi } from 'lightweight-charts';

interface PerformanceChartProps {
  data: Array<{
    timestamp: string;
    cumulativeReturn: number;
    dailyReturn: number;
    drawdown: number;
  }>;
}

export function PerformanceChart({ data }: PerformanceChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  
  useEffect(() => {
    if (!chartContainerRef.current || !data.length) return;
    
    // Create chart
    chartRef.current = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 400,
      layout: {
        background: { color: 'transparent' },
        textColor: '#9CA3AF',
      },
      grid: {
        vertLines: { color: '#374151' },
        horzLines: { color: '#374151' },
      },
      rightPriceScale: {
        borderColor: '#374151',
      },
      timeScale: {
        borderColor: '#374151',
      },
    });
    
    // Add cumulative return line
    const cumulativeReturnSeries = chartRef.current.addLineSeries({
      color: '#10B981',
      lineWidth: 2,
      title: 'Cumulative Return',
    });
    
    // Add drawdown area
    const drawdownSeries = chartRef.current.addAreaSeries({
      topColor: 'rgba(239, 68, 68, 0.3)',
      bottomColor: 'rgba(239, 68, 68, 0.1)',
      lineColor: '#EF4444',
      lineWidth: 1,
      title: 'Drawdown',
    });
    
    // Format data for chart
    const cumulativeData = data.map(item => ({
      time: item.timestamp,
      value: item.cumulativeReturn,
    }));
    
    const drawdownData = data.map(item => ({
      time: item.timestamp,
      value: -Math.abs(item.drawdown), // Negative for drawdown
    }));
    
    cumulativeReturnSeries.setData(cumulativeData);
    drawdownSeries.setData(drawdownData);
    
    // Handle resize
    const handleResize = () => {
      if (chartRef.current && chartContainerRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };
    
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
      }
    };
  }, [data]);
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Performance Chart</CardTitle>
      </CardHeader>
      <CardContent>
        <div ref={chartContainerRef} className="w-full h-[400px]" />
      </CardContent>
    </Card>
  );
}
```

```typescript
// components/analytics/date-range-picker.tsx
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface DateRangePickerProps {
  startDate: string;
  endDate: string;
  onDateRangeChange: (start: string, end: string) => void;
}

export function DateRangePicker({ 
  startDate, 
  endDate, 
  onDateRangeChange 
}: DateRangePickerProps) {
  const [localStartDate, setLocalStartDate] = useState(
    startDate.split('T')[0] // Convert to YYYY-MM-DD format
  );
  const [localEndDate, setLocalEndDate] = useState(
    endDate.split('T')[0]
  );
  
  const handleApply = () => {
    onDateRangeChange(
      new Date(localStartDate).toISOString(),
      new Date(localEndDate).toISOString()
    );
  };
  
  const setPresetRange = (days: number) => {
    const end = new Date();
    const start = new Date(end.getTime() - days * 24 * 60 * 60 * 1000);
    
    setLocalStartDate(start.toISOString().split('T')[0]);
    setLocalEndDate(end.toISOString().split('T')[0]);
    
    onDateRangeChange(start.toISOString(), end.toISOString());
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Date Range</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPresetRange(7)}
          >
            7D
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPresetRange(30)}
          >
            30D
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPresetRange(90)}
          >
            90D
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPresetRange(365)}
          >
            1Y
          </Button>
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="startDate">Start Date</Label>
            <Input
              id="startDate"
              type="date"
              value={localStartDate}
              onChange={(e) => setLocalStartDate(e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="endDate">End Date</Label>
            <Input
              id="endDate"
              type="date"
              value={localEndDate}
              onChange={(e) => setLocalEndDate(e.target.value)}
            />
          </div>
        </div>
        
        <Button onClick={handleApply} className="w-full">
          Apply Date Range
        </Button>
      </CardContent>
    </Card>
  );
}
```

#### Step 5: Create the Page

```typescript
// app/strategies/[id]/analytics/page.tsx
import { Metadata } from 'next';
import { StrategyAnalyticsContent } from '@/components/analytics/strategy-analytics-content';

interface Props {
  params: { id: string };
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  return {
    title: `Strategy Analytics - ${params.id}`,
    description: 'Detailed performance analytics for your trading strategy',
  };
}

export default function StrategyAnalyticsPage({ params }: Props) {
  return <StrategyAnalyticsContent strategyId={params.id} />;
}
```

```typescript
// components/analytics/strategy-analytics-content.tsx
'use client';

import { useStrategyAnalytics } from '@/hooks/use-strategy-analytics';
import { MetricsGrid } from './metrics-grid';
import { PerformanceChart } from './performance-chart';
import { DateRangePicker } from './date-range-picker';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';

interface Props {
  strategyId: string;
}

export function StrategyAnalyticsContent({ strategyId }: Props) {
  const {
    analytics,
    loading,
    error,
    dateRange,
    updateDateRange,
    exportData,
  } = useStrategyAnalytics(strategyId);
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner w-8 h-8"></div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="text-center p-8">
        <div className="text-destructive mb-4">
          Error loading analytics: {error.message}
        </div>
        <Button onClick={() => window.location.reload()}>
          Retry
        </Button>
      </div>
    );
  }
  
  if (!analytics) {
    return (
      <div className="text-center p-8">
        <div className="text-muted-foreground">
          No analytics data available
        </div>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Strategy Analytics</h1>
        <Button onClick={exportData} variant="outline">
          <Download className="w-4 h-4 mr-2" />
          Export Data
        </Button>
      </div>
      
      <div className="grid lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3 space-y-6">
          <MetricsGrid analytics={analytics} />
          <PerformanceChart data={analytics.performanceData} />
        </div>
        
        <div>
          <DateRangePicker
            startDate={dateRange.startDate}
            endDate={dateRange.endDate}
            onDateRangeChange={updateDateRange}
          />
        </div>
      </div>
    </div>
  );
}
```

### Example 2: Form Handling with Validation

```typescript
// components/forms/create-strategy-form.tsx
'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { toast } from '@/components/ui/toaster';
import { useStrategies } from '@/hooks/use-strategies';

// Form validation schema
const createStrategySchema = z.object({
  name: z.string().min(1, 'Name is required').max(100, 'Name too long'),
  description: z.string().min(10, 'Description must be at least 10 characters'),
  type: z.enum(['MANUAL', 'AUTOMATED', 'HYBRID']),
  riskLevel: z.enum(['LOW', 'MEDIUM', 'HIGH']),
  initialCapital: z.number().min(100, 'Minimum capital is $100'),
  maxDrawdown: z.number().min(1).max(50, 'Max drawdown must be between 1-50%'),
  tags: z.string().optional(),
});

type CreateStrategyFormData = z.infer<typeof createStrategySchema>;

export function CreateStrategyForm({ onSuccess }: { onSuccess?: () => void }) {
  const { createStrategy, creating } = useStrategies();
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
    reset,
  } = useForm<CreateStrategyFormData>({
    resolver: zodResolver(createStrategySchema),
    defaultValues: {
      type: 'MANUAL',
      riskLevel: 'MEDIUM',
      initialCapital: 1000,
      maxDrawdown: 10,
    },
  });
  
  const onSubmit = async (data: CreateStrategyFormData) => {
    try {
      const tags = data.tags ? data.tags.split(',').map(tag => tag.trim()) : [];
      
      await createStrategy({
        ...data,
        tags,
      });
      
      toast.success('Strategy created successfully!');
      reset();
      onSuccess?.();
    } catch (error) {
      toast.error('Failed to create strategy');
    }
  };
  
  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Create New Strategy</CardTitle>
      </CardHeader>
      
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="name">Strategy Name</Label>
              <Input
                id="name"
                {...register('name')}
                placeholder="Enter strategy name"
              />
              {errors.name && (
                <p className="text-sm text-destructive mt-1">
                  {errors.name.message}
                </p>
              )}
            </div>
            
            <div>
              <Label htmlFor="type">Strategy Type</Label>
              <Select onValueChange={(value) => setValue('type', value as any)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="MANUAL">Manual</SelectItem>
                  <SelectItem value="AUTOMATED">Automated</SelectItem>
                  <SelectItem value="HYBRID">Hybrid</SelectItem>
                </SelectContent>
              </Select>
              {errors.type && (
                <p className="text-sm text-destructive mt-1">
                  {errors.type.message}
                </p>
              )}
            </div>
          </div>
          
          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              {...register('description')}
              placeholder="Describe your strategy..."
              rows={4}
            />
            {errors.description && (
              <p className="text-sm text-destructive mt-1">
                {errors.description.message}
              </p>
            )}
          </div>
          
          <div className="grid md:grid-cols-3 gap-4">
            <div>
              <Label htmlFor="riskLevel">Risk Level</Label>
              <Select onValueChange={(value) => setValue('riskLevel', value as any)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select risk level" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="LOW">Low</SelectItem>
                  <SelectItem value="MEDIUM">Medium</SelectItem>
                  <SelectItem value="HIGH">High</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label htmlFor="initialCapital">Initial Capital ($)</Label>
              <Input
                id="initialCapital"
                type="number"
                {...register('initialCapital', { valueAsNumber: true })}
                placeholder="1000"
              />
              {errors.initialCapital && (
                <p className="text-sm text-destructive mt-1">
                  {errors.initialCapital.message}
                </p>
              )}
            </div>
            
            <div>
              <Label htmlFor="maxDrawdown">Max Drawdown (%)</Label>
              <Input
                id="maxDrawdown"
                type="number"
                {...register('maxDrawdown', { valueAsNumber: true })}
                placeholder="10"
              />
              {errors.maxDrawdown && (
                <p className="text-sm text-destructive mt-1">
                  {errors.maxDrawdown.message}
                </p>
              )}
            </div>
          </div>
          
          <div>
            <Label htmlFor="tags">Tags (comma-separated)</Label>
            <Input
              id="tags"
              {...register('tags')}
              placeholder="scalping, momentum, forex"
            />
          </div>
          
          <div className="flex gap-4">
            <Button type="submit" disabled={creating} className="flex-1">
              {creating ? 'Creating...' : 'Create Strategy'}
            </Button>
            <Button type="button" variant="outline" onClick={() => reset()}>
              Reset
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
```

This comprehensive guide covers every aspect of developing with the Alphintra frontend. You now have:

1. **Complete understanding** of the file system and routing
2. **Step-by-step instructions** for creating pages and components
3. **Real-world examples** of complex features
4. **Best practices** for code organization
5. **Detailed explanations** of how every part works together

Use this guide as your reference for building any feature in the Alphintra frontend!