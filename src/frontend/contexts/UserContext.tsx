'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { generateUUID } from '../utils/uuid';

export interface User {
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  role: 'ADMIN' | 'USER' | 'DEVELOPER';
  createdAt: string;
  lastLogin?: string;
}

interface UserContextType {
  user: User | null;
  setUser: (user: User | null) => void;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const UserContext = createContext<UserContextType>({
  user: null,
  setUser: () => {},
  isAuthenticated: false,
  isLoading: true,
});

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};

interface UserProviderProps {
  children: ReactNode;
}

export const UserProvider: React.FC<UserProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // For now, use dummy user data for testing
    // In production, this would fetch from authentication service
    const dummyUser: User = {
      id: generateUUID(),
      username: 'testuser',
      email: 'test@alphintra.com',
      firstName: 'Test',
      lastName: 'User',
      role: 'USER',
      createdAt: new Date().toISOString(),
      lastLogin: new Date().toISOString(),
    };

    // Simulate API call delay
    setTimeout(() => {
      setUser(dummyUser);
      setIsLoading(false);
    }, 1000);
  }, []);

  const isAuthenticated = !!user;

  const contextValue: UserContextType = {
    user,
    setUser,
    isAuthenticated,
    isLoading,
  };

  return (
    <UserContext.Provider value={contextValue}>
      {children}
    </UserContext.Provider>
  );
};