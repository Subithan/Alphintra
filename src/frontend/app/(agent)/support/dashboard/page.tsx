'use client';

import { useState, useEffect } from 'react';
// DEVELOPMENT: Commented out useAuth to bypass AuthProvider requirement
// import { useAuth } from '@/components/providers/AuthProvider';
import AgentDashboard from '@/components/support/agent/AgentDashboard';
import { Loader2 } from 'lucide-react';

export default function AgentDashboardPage() {
  // DEVELOPMENT: Mock user data instead of using useAuth
  // const { user, isLoading } = useAuth();
  const user = { 
    id: 'dev-agent', 
    email: 'dev-agent@alphintra.com', 
    name: 'Development Agent',
    roles: ['USER', 'SUPPORT_AGENT'],
    agentId: 'dev-agent-123',
    agentLevel: 'L2'
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

  // DEVELOPMENT: Disable auth and role checks - uncomment for production
  // if (!user || !user.roles?.includes('SUPPORT_AGENT')) {
  //   return (
  //     <div className="flex items-center justify-center min-h-screen">
  //       <div className="text-center">
  //         <h1 className="text-2xl font-bold text-gray-900 mb-4">Access Denied</h1>
  //         <p className="text-gray-600">You don't have permission to access the support agent dashboard.</p>
  //       </div>
  //     </div>
  //   );
  // }

  return (
    <div className="container mx-auto px-4 py-8">
      <AgentDashboard
        agentId={user?.agentId || user?.id || 'dev-agent-123'}
        agentName={user?.name || 'Development Agent'}
        agentLevel={user?.agentLevel || 'L2'}
      />
    </div>
  );
}