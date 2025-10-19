// file path: "D:\Alphintra\Alphintra\src\frontend\lib\api\auth-service-api.ts"

import axios from 'axios';
import { gatewayHttpBaseUrl } from '../config/gateway';
import { getToken } from '../auth';


// Types for Auth API
export interface User {
  id: number;
  username: string;
  email: string;
  firstName?: string;
  lastName?: string;
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

export interface RegisterCredentials {
  username: string;
  email: string;
  password: string;
  firstName?: string;
  lastName?: string;
}

export interface GoogleLoginCredentials {
  google_token: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}

export interface UpdateProfileRequest {
  firstName?: string;
  lastName?: string;
  phoneNumber?: string;
  address?: string;
}

export interface DeleteAccountRequest {
  password: string;
  confirmationText?: string;
}

export interface DeleteAccountResponse {
  message: string;
  username: string;
}

export class AuthServiceApiClient {
  private api: ReturnType<typeof axios.create>;

  constructor() {
    this.api = axios.create({
      baseURL: gatewayHttpBaseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.api.interceptors.request.use((config) => {
      const token = getToken();
      if (token) {
        config.headers = config.headers ?? {};
        if (!config.headers['Authorization']) {
          config.headers['Authorization'] = `Bearer ${token}`;
        }
      }
      return config;
    });

    if (process.env.NODE_ENV === 'development' && process.env.NEXT_PUBLIC_DEBUG_API === 'true') {
      console.log('🔧 AuthServiceApiClient Debug:', {
        baseUrl: this.api.defaults.baseURL,
      });
    }
  }

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await this.api.post<AuthResponse>('/api/auth/login', credentials);
    return response.data;
  }

  async register(credentials: RegisterCredentials): Promise<AuthResponse> {
    // Make sure keys match backend DTO fields
    const payload = {
      username: credentials.username,
      email: credentials.email,
      password: credentials.password,
      firstName: credentials.firstName,
      lastName: credentials.lastName,
    };

    const response = await this.api.post<AuthResponse>('/api/auth/register', payload);
    return response.data;
  }

  async googleLogin(credentials: GoogleLoginCredentials): Promise<AuthResponse> {
    const response = await this.api.post<AuthResponse>('/api/auth/google', credentials);
    return response.data;
  }

  async getProfile(): Promise<User> {
    const response = await this.api.get<User>('/api/users/me');
    return response.data;
  }

  async updateProfile(data: UpdateProfileRequest): Promise<User> {
    const response = await this.api.put<User>('/api/users/me', data);
    return response.data;
  }

  async deleteAccount(): Promise<DeleteAccountResponse> {
    const response = await this.api.delete<DeleteAccountResponse>('/api/users/account');
    return response.data;
  }
}

export const authServiceApiClient = new AuthServiceApiClient();
