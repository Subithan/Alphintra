'use client';

import { useEffect } from 'react';

export function EnvDebug() {
  // Only show debug info when explicitly enabled
  const showDebug = process.env.NEXT_PUBLIC_DEBUG_UI === 'true';
  
  useEffect(() => {
    if (showDebug) {
      console.log('🔍 Environment Debug:', {
        NEXT_PUBLIC_MOCK_API: process.env.NEXT_PUBLIC_MOCK_API,
        NODE_ENV: process.env.NODE_ENV,
        NEXT_PUBLIC_GATEWAY_URL: process.env.NEXT_PUBLIC_GATEWAY_URL,
      });
    }
  }, [showDebug]);

  if (!showDebug) {
    return null;
  }

  return (
    <div className="fixed top-4 right-4 bg-black text-white p-2 text-xs rounded opacity-75 z-50">
      <div>Mock API: {process.env.NEXT_PUBLIC_MOCK_API}</div>
      <div>NODE_ENV: {process.env.NODE_ENV}</div>
      <div>Gateway: {process.env.NEXT_PUBLIC_GATEWAY_URL}</div>
    </div>
  );
}
