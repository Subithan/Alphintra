'use client';

import { Suspense } from 'react';
import { EnhancedIDE } from '@/components/ide/EnhancedIDE';

export default function IDEPage() {
  return (
    <div className="h-screen w-full">
      <Suspense fallback={
        <div className="h-full w-full flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading Enhanced IDE...</p>
          </div>
        </div>
      }>
        <EnhancedIDE />
      </Suspense>
    </div>
  );
}