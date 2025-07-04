const TOKEN_KEY = 'alphintra_auth_token';
const USER_KEY = 'alphintra_user';

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: 'USER' | 'ADMIN' | 'PREMIUM';
  isVerified: boolean;
  twoFactorEnabled: boolean;
  createdAt: string;
  updatedAt: string;
}

// Token management
export const getToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
};

export const setToken = (token: string): void => {
  if (typeof window === 'undefined') return;
  localStorage.setItem(TOKEN_KEY, token);
};

export const removeToken = (): void => {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};

// User management
export const getUser = (): User | null => {
  if (typeof window === 'undefined') return null;
  const userStr = localStorage.getItem(USER_KEY);
  if (!userStr) return null;
  
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
};

export const setUser = (user: User): void => {
  if (typeof window === 'undefined') return;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
};

export const removeUser = (): void => {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(USER_KEY);
};

// Auth state checks
export const isAuthenticated = (): boolean => {
  return getToken() !== null;
};

export const isTokenExpired = (token: string): boolean => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const currentTime = Date.now() / 1000;
    return payload.exp < currentTime;
  } catch {
    return true;
  }
};

export const shouldRefreshToken = (token: string): boolean => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const currentTime = Date.now() / 1000;
    const timeUntilExpiry = payload.exp - currentTime;
    // Refresh if token expires in less than 5 minutes
    return timeUntilExpiry < 300;
  } catch {
    return false;
  }
};

// Logout utility
export const logout = (): void => {
  removeToken();
  removeUser();
  
  // Redirect to login page
  if (typeof window !== 'undefined') {
    window.location.href = '/login';
  }
};

// Route protection utilities
export const requireAuth = (): boolean => {
  const token = getToken();
  
  if (!token || isTokenExpired(token)) {
    logout();
    return false;
  }
  
  return true;
};

export const requireRole = (requiredRole: User['role']): boolean => {
  if (!requireAuth()) return false;
  
  const user = getUser();
  if (!user) return false;
  
  const roleHierarchy: Record<User['role'], number> = {
    'USER': 1,
    'PREMIUM': 2,
    'ADMIN': 3,
  };
  
  return roleHierarchy[user.role] >= roleHierarchy[requiredRole];
};