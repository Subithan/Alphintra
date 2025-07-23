//file path :"D:\Alphintra\Alphintra\src\frontend\lib\api\auth-service-api.ts"

import { BaseApiClient } from './api-client';

// Types for Auth API
export interface User {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  date_of_birth?: string;
  phone_number?: string;
  address?: string;
  kyc_status: string;
  created_at: string;
  updated_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface registerCredentials {
  username: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

export interface GoogleLoginCredentials {
  google_token: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}

export class AuthServiceApiClient extends BaseApiClient {
  constructor() {
    super({
      baseUrl: process.env.NEXT_PUBLIC_AUTH_API_URL || 'http://localhost:8009',
    });

    if (process.env.NODE_ENV === 'development' && process.env.NEXT_PUBLIC_DEBUG_API === 'true') {
      console.log('🔧 AuthServiceApiClient Debug:', {
        baseUrl: this.config.baseUrl,
      });
    }
  }

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    return this.requestWithRetry<AuthResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  async register(credentials: registerCredentials): Promise<AuthResponse> {
    return this.requestWithRetry<AuthResponse>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  async googleLogin(credentials: GoogleLoginCredentials): Promise<AuthResponse> {
    return this.requestWithRetry<AuthResponse>('/api/auth/google', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }
}

export const authServiceApiClient = new AuthServiceApiClient();