'use client';

import { useState, useEffect } from 'react';
// DEVELOPMENT: Commented out useAuth to bypass AuthProvider requirement
// import { useAuth } from '@/hooks/useAuth';
import TicketAssignmentPanel from '@/components/support/agent/TicketAssignmentPanel';
import { AgentLevel } from '@/lib/api/customer-support-api';
import { Loader2 } from 'lucide-react';

// Disable static generation for this page as it requires authentication
export const dynamic = 'force-dynamic';

export default function TicketAssignmentPage() {
  // DEVELOPMENT: Mock user data instead of using useAuth
  // const { user, isLoading } = useAuth();
  const user = {
    id: 'dev-agent',
    email: 'dev-agent@alphintra.com',
    name: 'Development Agent',
    role: 'agent'
  };
  const isLoading = false;
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
          <p className="text-gray-600">You don't have permission to access ticket assignment.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <TicketAssignmentPanel
        currentAgentId={user.agentId || user.id}
        currentAgentLevel={user.agentLevel || AgentLevel.L1}
      />
    </div>
  );
}