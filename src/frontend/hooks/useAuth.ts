'use client';

import { useState, useEffect, createContext, useContext } from 'react';
import { generateUUID, isValidUUID, stringToUUID } from '../utils/uuid';

export interface User {
  id: string;
  email: string;
  name: string;
  roles: string[];
  agentId?: string;
  agentLevel?: string;
  isActive: boolean;
  lastLogin?: string;
  preferences?: {
    theme: 'light' | 'dark';
    notifications: boolean;
    language: string;
  };
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Mock authentication hook for development
// In production, this would integrate with your authentication service
export const useAuthHook = (): AuthContextType => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate loading user from localStorage or API
    const loadUser = async () => {
      try {
        const storedUser = localStorage.getItem('auth_user');
        if (storedUser) {
          const userData = JSON.parse(storedUser);
          // Migrate old user data with invalid UUID to proper format
          if (!isValidUUID(userData.id)) {
            userData.id = stringToUUID(userData.id);
            localStorage.setItem('auth_user', JSON.stringify(userData));
          }
          setUser(userData);
        } else {
          // For development, create a mock user
          const mockUser: User = {
            id: '123e4567-e89b-12d3-a456-426614174000',
            email: 'john.doe@alphintra.com',
            name: 'John Doe',
            roles: ['USER', 'SUPPORT_AGENT'],
            agentId: 'agent-123',
            agentLevel: 'L2',
            isActive: true,
            lastLogin: new Date().toISOString(),
            preferences: {
              theme: 'light',
              notifications: true,
              language: 'en'
            }
          };
          setUser(mockUser);
          localStorage.setItem('auth_user', JSON.stringify(mockUser));
        }
      } catch (error) {
        console.error('Failed to load user:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadUser();
  }, []);

  const login = async (email: string, password: string): Promise<void> => {
    setIsLoading(true);
    try {
      // Mock login API call
      // In production, this would call your authentication API
      const mockUser: User = {
        id: generateUUID(),
        email,
        name: email.split('@')[0].replace('.', ' ').replace(/\b\w/g, l => l.toUpperCase()),
        roles: email.includes('agent') ? ['USER', 'SUPPORT_AGENT'] : ['USER'],
        agentId: email.includes('agent') ? 'agent-123' : undefined,
        agentLevel: email.includes('manager') ? 'L4_MANAGER' : email.includes('specialist') ? 'L3_SPECIALIST' : 'L2',
        isActive: true,
        lastLogin: new Date().toISOString(),
        preferences: {
          theme: 'light',
          notifications: true,
          language: 'en'
        }
      };

      setUser(mockUser);
      localStorage.setItem('auth_user', JSON.stringify(mockUser));
      localStorage.setItem('auth_token', 'mock-jwt-token');
    } catch (error) {
      throw new Error('Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    setUser(null);
    localStorage.removeItem('auth_user');
    localStorage.removeItem('auth_token');
  };

  const refreshUser = async (): Promise<void> => {
    // In production, this would refresh user data from the API
    const storedUser = localStorage.getItem('auth_user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  };

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    refreshUser
  };
};