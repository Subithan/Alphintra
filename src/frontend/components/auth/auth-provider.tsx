// file path "D:\Alphintra\Alphintra\src\frontend\components\auth\auth-provider.tsx"

'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, getToken, getUser, setUser, removeToken, removeUser, isTokenExpired } from '@/lib/auth';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
  updateUser: (user: User) => void;
  refreshToken: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUserState] = useState<User | null>(null);
  const [token, setTokenState] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = Boolean(user && token);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = () => {
      const storedToken = getToken();
      const storedUser = getUser();

      if (storedToken && storedUser) {
        // Check if token is expired
        if (isTokenExpired(storedToken)) {
          // Token expired, clear auth state
          removeToken();
          removeUser();
          setUserState(null);
          setTokenState(null);
        } else {
          // Token valid, set auth state
          setTokenState(storedToken);
          setUserState(storedUser);
        }
      }

      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = (newToken: string, newUser: User) => {
    setTokenState(newToken);
    setUserState(newUser);
    setUser(newUser);
    
    // Store in localStorage (handled by auth utilities)
    if (typeof window !== 'undefined') {
      localStorage.setItem('alphintra_auth_token', newToken);
      localStorage.setItem('alphintra_user', JSON.stringify(newUser));
    }
  };

  const logout = () => {
    setTokenState(null);
    setUserState(null);
    removeToken();
    removeUser();
    
    // Redirect to login page
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  };

  const updateUser = (updatedUser: User) => {
    setUserState(updatedUser);
    setUser(updatedUser);
  };

  const refreshToken = async () => {
    try {
      // This would typically make an API call to refresh the token
      // For now, we'll just check if the current token is still valid
      const currentToken = getToken();
      if (currentToken && isTokenExpired(currentToken)) {
        logout();
      }
    } catch (error) {
      console.error('Error refreshing token:', error);
      logout();
    }
  };

  // Set up token refresh interval
  useEffect(() => {
    if (!isAuthenticated) return;

    const interval = setInterval(() => {
      refreshToken();
    }, 60000); // Check every minute

    return () => clearInterval(interval);
  }, [isAuthenticated]);

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated,
    login,
    logout,
    updateUser,
    refreshToken,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}