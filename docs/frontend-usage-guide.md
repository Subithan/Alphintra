# Alphintra Frontend - Comprehensive Usage Guide

## Table of Contents
1. [Project Overview](#project-overview)
2. [Getting Started](#getting-started)
3. [Project Structure](#project-structure)
4. [Architecture Guide](#architecture-guide)
5. [Development Workflow](#development-workflow)
6. [Component Development](#component-development)
7. [State Management](#state-management)
8. [Authentication System](#authentication-system)
9. [Styling Guide](#styling-guide)
10. [GraphQL Integration](#graphql-integration)
11. [API Integration](#api-integration)
12. [Testing Guidelines](#testing-guidelines)
13. [Deployment](#deployment)
14. [Troubleshooting](#troubleshooting)
15. [Best Practices](#best-practices)

## Project Overview

Alphintra is a professional AI-powered trading platform built with Next.js 14+, featuring:
- **Framework**: Next.js 14+ with App Router
- **Language**: TypeScript for type safety
- **Styling**: Tailwind CSS with custom design system
- **State Management**: Zustand for global state
- **Data Fetching**: Apollo GraphQL with real-time subscriptions
- **Authentication**: JWT-based authentication system
- **UI Components**: Custom component library

## Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Git

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd src/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Available Scripts

```bash
# Development
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript type checking
```

## Project Structure

```
src/frontend/
├── app/                     # Next.js App Router pages
│   ├── globals.css         # Global styles
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Home page
├── components/             # React components
│   ├── auth/              # Authentication components
│   ├── landing/           # Landing page components
│   ├── ui/                # Reusable UI components
│   └── providers.tsx      # Global providers
├── lib/                   # Utility libraries
│   ├── stores/           # Zustand stores
│   ├── apollo-client.ts  # GraphQL client setup
│   ├── auth.ts           # Authentication utilities
│   └── utils.ts          # General utilities
├── public/               # Public assets
├── package.json         # Dependencies and scripts
├── tailwind.config.ts   # Tailwind configuration
├── tsconfig.json        # TypeScript configuration
└── next.config.js       # Next.js configuration
```

## Architecture Guide

### 1. App Router Structure
The application uses Next.js 14+ App Router with the following routing strategy:

```typescript
app/
├── page.tsx                 # Home page (/)
├── layout.tsx              # Root layout
├── (auth)/                 # Route group for auth pages
│   ├── login/
│   ├── register/
│   └── verify/
└── (dashboard)/           # Route group for authenticated pages
    ├── dashboard/
    ├── strategies/
    ├── marketplace/
    └── settings/
```

### 2. Component Architecture
Components are organized by feature and reusability:

```typescript
components/
├── ui/                    # Reusable UI components
│   ├── button.tsx
│   ├── input.tsx
│   └── toaster.tsx
├── auth/                  # Authentication-specific components
├── trading/               # Trading-specific components
└── layout/                # Layout components
```

## Development Workflow

### 1. Creating New Components

```typescript
// components/ui/example-component.tsx
import React from 'react';
import { cn } from '@/lib/utils';

interface ExampleComponentProps {
  title: string;
  variant?: 'default' | 'primary';
  className?: string;
  children?: React.ReactNode;
}

export function ExampleComponent({
  title,
  variant = 'default',
  className,
  children,
}: ExampleComponentProps) {
  return (
    <div className={cn(
      'base-styles',
      variant === 'primary' && 'primary-styles',
      className
    )}>
      <h2>{title}</h2>
      {children}
    </div>
  );
}
```

### 2. Adding New Pages

```typescript
// app/new-page/page.tsx
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'New Page - Alphintra',
  description: 'Description of the new page',
};

export default function NewPage() {
  return (
    <div>
      <h1>New Page</h1>
      {/* Page content */}
    </div>
  );
}
```

### 3. Creating Layouts

```typescript
// app/new-section/layout.tsx
export default function NewSectionLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="section-layout">
      <nav>Section Navigation</nav>
      <main>{children}</main>
    </div>
  );
}
```

## Component Development

### 1. UI Component Pattern

```typescript
// components/ui/card.tsx
import { cn } from '@/lib/utils';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'outlined';
}

export function Card({ className, variant = 'default', ...props }: CardProps) {
  return (
    <div
      className={cn(
        'trading-card', // Base class from globals.css
        variant === 'outlined' && 'border-2',
        className
      )}
      {...props}
    />
  );
}

// Usage
<Card variant="outlined" className="p-6">
  <h3>Card Title</h3>
  <p>Card content</p>
</Card>
```

### 2. Trading-Specific Components

```typescript
// components/trading/profit-loss-indicator.tsx
import { cn } from '@/lib/utils';
import { formatCurrency, formatPercentage } from '@/lib/utils';

interface ProfitLossIndicatorProps {
  value: number;
  percentage: number;
  showCurrency?: boolean;
  className?: string;
}

export function ProfitLossIndicator({
  value,
  percentage,
  showCurrency = true,
  className,
}: ProfitLossIndicatorProps) {
  const isProfit = value >= 0;
  
  return (
    <div className={cn(
      'flex items-center gap-2',
      isProfit ? 'profit-text' : 'loss-text',
      className
    )}>
      {showCurrency && (
        <span className="font-medium">
          {formatCurrency(Math.abs(value))}
        </span>
      )}
      <span className="text-sm">
        ({isProfit ? '+' : '-'}{formatPercentage(Math.abs(percentage))})
      </span>
    </div>
  );
}
```

## State Management

### 1. Zustand Store Pattern

```typescript
// lib/stores/example-store.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ExampleState {
  count: number;
  items: string[];
  isLoading: boolean;
}

interface ExampleActions {
  increment: () => void;
  addItem: (item: string) => void;
  setLoading: (loading: boolean) => void;
  reset: () => void;
}

type ExampleStore = ExampleState & ExampleActions;

export const useExampleStore = create<ExampleStore>()(
  persist(
    (set, get) => ({
      // State
      count: 0,
      items: [],
      isLoading: false,

      // Actions
      increment: () => set((state) => ({ count: state.count + 1 })),
      
      addItem: (item: string) => set((state) => ({
        items: [...state.items, item]
      })),
      
      setLoading: (loading: boolean) => set({ isLoading: loading }),
      
      reset: () => set({ count: 0, items: [], isLoading: false }),
    }),
    {
      name: 'example-store',
      partialize: (state) => ({ count: state.count, items: state.items }),
    }
  )
);
```

### 2. Using Stores in Components

```typescript
// components/example-component.tsx
import { useExampleStore } from '@/lib/stores/example-store';

export function ExampleComponent() {
  const { count, items, isLoading, increment, addItem } = useExampleStore();
  
  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={increment}>Increment</button>
      <button onClick={() => addItem('New Item')}>Add Item</button>
      {isLoading && <p>Loading...</p>}
    </div>
  );
}
```

### 3. Trading Store Usage

```typescript
// Using the trading store
import { useTradingStore, useTradingSelectors } from '@/lib/stores/trading-store';

export function PortfolioSummary() {
  const { portfolio, setSelectedSymbol } = useTradingStore();
  const { totalPortfolioValue, portfolioChangePercent } = useTradingSelectors();
  
  return (
    <div className="trading-card">
      <h3>Portfolio</h3>
      <p>Total Value: {formatCurrency(totalPortfolioValue)}</p>
      <ProfitLossIndicator 
        value={portfolio?.dailyPnL || 0}
        percentage={portfolioChangePercent}
      />
    </div>
  );
}
```

## Authentication System

### 1. Auth Context Usage

```typescript
// components/auth/protected-route.tsx
import { useAuth } from '@/components/auth/auth-provider';
import { redirect } from 'next/navigation';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) {
    return <div>Loading...</div>;
  }
  
  if (!isAuthenticated) {
    redirect('/login');
  }
  
  return <>{children}</>;
}
```

### 2. Login Component Example

```typescript
// components/auth/login-form.tsx
'use client';

import { useState } from 'react';
import { useAuth } from '@/components/auth/auth-provider';
import { Button } from '@/components/ui/button';
import { toast } from '@/components/ui/toaster';

export function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      // API call to authenticate
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        login(data.token, data.user);
        toast.success('Login successful!');
      } else {
        toast.error(data.message);
      }
    } catch (error) {
      toast.error('Login failed');
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="form-field">
        <label className="form-label">Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="form-input"
          required
        />
      </div>
      
      <div className="form-field">
        <label className="form-label">Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="form-input"
          required
        />
      </div>
      
      <Button type="submit" disabled={isLoading} className="w-full">
        {isLoading ? 'Signing in...' : 'Sign In'}
      </Button>
    </form>
  );
}
```

### 3. Auth Utilities

```typescript
// Using auth utilities
import { requireAuth, requireRole, logout } from '@/lib/auth';

// In a component or page
useEffect(() => {
  if (!requireAuth()) {
    // User will be redirected to login
    return;
  }
  
  if (!requireRole('PREMIUM')) {
    // Handle insufficient permissions
    toast.error('Premium subscription required');
    return;
  }
  
  // User is authenticated and has required role
}, []);

// Logout function
const handleLogout = () => {
  logout(); // Will clear tokens and redirect
};
```

## Styling Guide

### 1. Tailwind CSS Classes

The project uses custom CSS classes defined in `globals.css`:

```css
/* Trading-specific utility classes */
.profit-text      /* Green text for profits */
.loss-text        /* Red text for losses */
.neutral-text     /* Muted text for neutral values */
.trading-card     /* Base card styling */
.metric-card      /* Card with hover effects */
.sidebar-item     /* Navigation item styling */
.chart-container  /* Chart wrapper styling */
```

### 2. Custom Color Palette

```typescript
// Available in Tailwind config
colors: {
  profit: {
    DEFAULT: 'hsl(142, 76%, 36%)',
    light: 'hsl(142, 76%, 46%)',
    dark: 'hsl(142, 76%, 26%)',
  },
  loss: {
    DEFAULT: 'hsl(0, 84%, 60%)',
    light: 'hsl(0, 84%, 70%)',
    dark: 'hsl(0, 84%, 50%)',
  }
}
```

### 3. Component Styling Pattern

```typescript
// Using cn utility for conditional classes
import { cn } from '@/lib/utils';

<div className={cn(
  'base-class',
  condition && 'conditional-class',
  variant === 'primary' && 'primary-variant',
  className // Allow custom overrides
)} />
```

### 4. Responsive Design

```typescript
// Mobile-first responsive classes
<div className={cn(
  'w-full p-4',           // Base mobile styles
  'md:w-1/2 md:p-6',      // Tablet styles
  'lg:w-1/3 lg:p-8',      // Desktop styles
  'xl:w-1/4'              // Large desktop
)} />
```

## GraphQL Integration

### 1. Apollo Client Setup

The Apollo client is configured in `lib/apollo-client.ts` with:
- HTTP link for queries/mutations
- WebSocket link for subscriptions
- Authentication handling
- Error handling with automatic token refresh

### 2. Query Example

```typescript
// hooks/use-portfolio.ts
import { useQuery } from '@apollo/client';
import { gql } from '@apollo/client';

const GET_PORTFOLIO = gql`
  query GetPortfolio {
    portfolio {
      id
      totalValue
      cashBalance
      dailyPnL
      positions {
        id
        symbol
        quantity
        averagePrice
        currentPrice
        unrealizedPnL
      }
    }
  }
`;

export function usePortfolio() {
  const { data, loading, error, refetch } = useQuery(GET_PORTFOLIO, {
    pollInterval: 5000, // Poll every 5 seconds
    errorPolicy: 'all',
  });
  
  return {
    portfolio: data?.portfolio,
    loading,
    error,
    refetch,
  };
}
```

### 3. Mutation Example

```typescript
// hooks/use-create-strategy.ts
import { useMutation } from '@apollo/client';
import { gql } from '@apollo/client';

const CREATE_STRATEGY = gql`
  mutation CreateStrategy($input: CreateStrategyInput!) {
    createStrategy(input: $input) {
      id
      name
      description
      status
    }
  }
`;

export function useCreateStrategy() {
  const [createStrategy, { loading, error }] = useMutation(CREATE_STRATEGY, {
    refetchQueries: ['GetStrategies'], // Refetch strategies list
  });
  
  const handleCreateStrategy = async (strategyData: any) => {
    try {
      const result = await createStrategy({
        variables: { input: strategyData },
      });
      return result.data.createStrategy;
    } catch (err) {
      console.error('Error creating strategy:', err);
      throw err;
    }
  };
  
  return { createStrategy: handleCreateStrategy, loading, error };
}
```

### 4. Subscription Example

```typescript
// hooks/use-market-data.ts
import { useSubscription } from '@apollo/client';
import { gql } from '@apollo/client';

const MARKET_DATA_SUBSCRIPTION = gql`
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

export function useMarketDataSubscription(symbols: string[]) {
  const { data, loading, error } = useSubscription(MARKET_DATA_SUBSCRIPTION, {
    variables: { symbols },
    onData: ({ data }) => {
      // Handle real-time updates
      console.log('Market data update:', data.data);
    },
  });
  
  return { marketData: data?.marketDataUpdates, loading, error };
}
```

## API Integration

### 1. REST API Calls

```typescript
// lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

class ApiClient {
  private getAuthHeaders() {
    const token = localStorage.getItem('alphintra_auth_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  }
  
  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: this.getAuthHeaders(),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  }
  
  async post<T>(endpoint: string, data: any): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  }
}

export const apiClient = new ApiClient();
```

### 2. Using API Client

```typescript
// hooks/use-api.ts
import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';

export function useApi<T>(endpoint: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await apiClient.get<T>(endpoint);
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [endpoint]);
  
  return { data, loading, error };
}
```

## Testing Guidelines

### 1. Component Testing Setup

```bash
# Install testing dependencies
npm install --save-dev @testing-library/react @testing-library/jest-dom jest-environment-jsdom
```

```typescript
// __tests__/components/ui/button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '@/components/ui/button';

describe('Button Component', () => {
  it('renders correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });
  
  it('handles click events', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
  
  it('applies correct variant classes', () => {
    render(<Button variant="destructive">Delete</Button>);
    expect(screen.getByText('Delete')).toHaveClass('btn-destructive');
  });
});
```

### 2. Testing Authentication

```typescript
// __tests__/lib/auth.test.ts
import { getToken, setToken, removeToken, isAuthenticated } from '@/lib/auth';

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('Auth Utils', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  it('should set and get token', () => {
    const token = 'test-token';
    setToken(token);
    
    expect(localStorageMock.setItem).toHaveBeenCalledWith('alphintra_auth_token', token);
  });
  
  it('should check authentication status', () => {
    localStorageMock.getItem.mockReturnValue('valid-token');
    expect(isAuthenticated()).toBe(true);
    
    localStorageMock.getItem.mockReturnValue(null);
    expect(isAuthenticated()).toBe(false);
  });
});
```

### 3. Testing Zustand Stores

```typescript
// __tests__/stores/trading-store.test.ts
import { renderHook, act } from '@testing-library/react';
import { useTradingStore } from '@/lib/stores/trading-store';

describe('Trading Store', () => {
  it('should update portfolio', () => {
    const { result } = renderHook(() => useTradingStore());
    
    const mockPortfolio = {
      totalValue: 10000,
      cashBalance: 5000,
      positions: [],
      dailyPnL: 500,
      totalPnL: 1000,
    };
    
    act(() => {
      result.current.setPortfolio(mockPortfolio);
    });
    
    expect(result.current.portfolio).toEqual(mockPortfolio);
  });
});
```

## Deployment

### 1. Build Process

```bash
# Build the application
npm run build

# Test the production build locally
npm run start
```

### 2. Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_URL=https://api.alphintra.com
NEXT_PUBLIC_WS_URL=wss://api.alphintra.com
NEXT_PUBLIC_APP_ENV=production
```

### 3. Deployment Checklist

- [ ] Environment variables configured
- [ ] Build passes without errors
- [ ] Type checking passes
- [ ] Tests pass
- [ ] Performance audit completed
- [ ] Security headers configured
- [ ] Analytics configured

## Troubleshooting

### Common Issues

1. **Build Errors**
   ```bash
   # Clear Next.js cache
   rm -rf .next
   npm run build
   ```

2. **Type Errors**
   ```bash
   # Run type checking
   npm run type-check
   ```

3. **Apollo Client Errors**
   - Check network connectivity
   - Verify GraphQL endpoint
   - Check authentication tokens

4. **Styling Issues**
   - Verify Tailwind CSS classes
   - Check custom CSS imports
   - Validate responsive breakpoints

### Debug Mode

```typescript
// Enable debug mode for Apollo Client
export const apolloClient = new ApolloClient({
  // ... other config
  connectToDevTools: process.env.NODE_ENV === 'development',
});

// Debug Zustand stores
import { devtools } from 'zustand/middleware';

export const useExampleStore = create<ExampleStore>()(
  devtools(
    (set, get) => ({
      // ... store implementation
    }),
    { name: 'example-store' }
  )
);
```

## Best Practices

### 1. Component Design

- Use TypeScript interfaces for props
- Implement proper error boundaries
- Follow the single responsibility principle
- Use composition over inheritance
- Implement proper loading states

### 2. State Management

- Keep stores focused and small
- Use selectors for computed values
- Implement proper error handling
- Use persistence strategically

### 3. Performance

- Use React.memo for expensive components
- Implement proper code splitting
- Optimize bundle size
- Use proper image optimization
- Implement proper caching strategies

### 4. Security

- Validate all user inputs
- Implement proper authentication checks
- Use HTTPS in production
- Sanitize data before rendering
- Implement proper CORS policies

### 5. Accessibility

- Use semantic HTML elements
- Implement proper ARIA labels
- Ensure keyboard navigation
- Maintain proper color contrast
- Test with screen readers

### 6. Code Organization

- Use consistent naming conventions
- Implement proper folder structure
- Use absolute imports with path aliases
- Keep components small and focused
- Document complex logic

## Conclusion

This guide covers the essential aspects of developing with the Alphintra frontend. The architecture is designed to be scalable, maintainable, and performant. Follow the patterns and best practices outlined here to ensure consistent development across the team.

For additional help, refer to:
- [Next.js Documentation](https://nextjs.org/docs)
- [TypeScript Documentation](https://www.typescriptlang.org/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Apollo Client Documentation](https://www.apollographql.com/docs)
- [Zustand Documentation](https://zustand-demo.pmnd.rs)