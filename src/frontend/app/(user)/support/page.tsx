'use client';

import { useState, useEffect } from 'react';
// DEVELOPMENT: Commented out useAuth to bypass AuthProvider requirement
// import { useAuth } from '@/components/providers/AuthProvider';
import UserSupportDashboard from '@/components/support/user/UserSupportDashboard';
import { Loader2 } from 'lucide-react';

export default function SupportPage() {
  // DEVELOPMENT: Mock user data instead of using useAuth
  // const { user, isLoading } = useAuth();
  const user = { id: 'dev-user', email: 'dev@alphintra.com', name: 'Development User' };
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

  // DEVELOPMENT: Disable auth check - uncomment for production
  // if (!user) {
  //   return (
  //     <div className="flex items-center justify-center min-h-screen">
  //       <div className="text-center">
  //         <h1 className="text-2xl font-bold text-gray-900 mb-4">Access Denied</h1>
  //         <p className="text-gray-600">Please log in to access customer support.</p>
  //       </div>
  //     </div>
  //   );
  // }

  return (
    <div className="container mx-auto px-4 py-8">
      <UserSupportDashboard
        userId={user?.id || 'dev-user'}
        userEmail={user?.email || 'dev@alphintra.com'}
        userName={user?.name || 'Development User'}
      />
    </div>
  );
}