import type { Metadata } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { Providers } from '@/components/providers';
import { Toaster } from '@/components/ui/toaster';
import AuthProvider from '@/components/providers/AuthProvider';
import SupportWebSocketProvider from '@/components/providers/SupportWebSocketProvider';
import { Toaster as HotToaster } from 'react-hot-toast';

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
    template: '%s | Alphintra',
  },
  description:
    'Professional AI-powered trading platform with strategy creation, backtesting, and automated trading capabilities.',
  keywords: [
    'trading',
    'algorithmic trading',
    'AI trading',
    'strategy creation',
    'backtesting',
    'cryptocurrency',
    'stocks',
    'forex',
  ],
  authors: [
    {
      name: 'Alphintra',
      url: 'https://alphintra.com',
    },
  ],
  creator: 'Alphintra',
  metadataBase: new URL('https://alphintra.com'),
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://alphintra.com',
    title: 'Alphintra - AI-Powered Trading Platform',
    description:
      'Professional AI-powered trading platform with strategy creation, backtesting, and automated trading capabilities.',
    siteName: 'Alphintra',
    images: [
      {
        url: '/og.png',
        width: 1200,
        height: 630,
        alt: 'Alphintra - AI-Powered Trading Platform',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Alphintra - AI-Powered Trading Platform',
    description:
      'Professional AI-powered trading platform with strategy creation, backtesting, and automated trading capabilities.',
    images: ['/og.png'],
    creator: '@alphintra',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  manifest: '/site.webmanifest',
  icons: {
    icon: '/favicon.ico',
    shortcut: '/favicon-16x16.png',
    apple: '/apple-touch-icon.png',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`} suppressHydrationWarning>
      <head>
        <link rel="icon" href="/logo.png" />
      </head>
      <body className="min-h-screen bg-background font-sans antialiased">
        <AuthProvider>
          <SupportWebSocketProvider>
            <Providers>
              {children}
              <Toaster />
              
              {/* Support system toast notifications */}
              <HotToaster
                position="top-right"
                toastOptions={{
                  duration: 4000,
                  style: {
                    background: '#363636',
                    color: '#fff',
                  },
                  success: {
                    style: {
                      background: '#10b981',
                    },
                  },
                  error: {
                    style: {
                      background: '#ef4444',
                    },
                  },
                }}
              />
            </Providers>
          </SupportWebSocketProvider>
        </AuthProvider>
      </body>
    </html>
  );
}