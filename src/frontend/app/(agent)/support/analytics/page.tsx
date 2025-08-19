'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import SupportAnalyticsDashboard from '@/components/support/analytics/SupportAnalyticsDashboard';
import { Loader2 } from 'lucide-react';

export default function SupportAnalyticsPage() {
  const { user, isLoading } = useAuth();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  if (!user || !user.roles?.includes('SUPPORT_AGENT')) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Access Denied</h1>
          <p className="text-gray-600">You don't have permission to access support analytics.</p>
        </div>
      </div>
    );
  }

  const isManagerView = user.roles?.includes('SUPPORT_MANAGER') || user.agentLevel === 'L4_MANAGER';

  return (
    <div className="container mx-auto px-4 py-8">
      <SupportAnalyticsDashboard
        isManagerView={isManagerView}
        agentId={!isManagerView ? (user.agentId || user.id) : undefined}
      />
    </div>
  );
}