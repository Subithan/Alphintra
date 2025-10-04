// Central exports for all API services
// This provides a clean interface for components to import API services

// Import API services for local use
import { strategyApi } from './strategy-api';
import { marketDataApi } from './market-data-api';
import { riskManagementApi } from './risk-management-api';
import { noCodeApiClient } from './no-code-api';

// Re-export for external use
export { BaseApiClient, ApiError, type ApiConfig, type ApiResponse } from './api-client';
export { strategyApi, type StrategyData, type BacktestRequest, type BacktestResult } from './strategy-api';
export { marketDataApi, type MarketDataPoint, type DataSourceConfig, type DataQualityReport } from './market-data-api';
export { riskManagementApi, type RiskProfile, type RiskAlert, type PositionRiskAssessment } from './risk-management-api';
export { 
  noCodeApiClient, 
  NoCodeApiClient,
  type Workflow, 
  type WorkflowCreate, 
  type WorkflowUpdate,
  type WorkflowData,
  type WorkflowNode,
  type WorkflowEdge,
  type Execution,
  type ExecutionConfig,
  type CompilationResult,
  type Component,
  type Template,
  type WorkflowFilters,
  type ComponentFilters,
  type TemplateFilters
} from './no-code-api';

// Authentication API service
export interface AuthUser {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'trader' | 'viewer';
  permissions: string[];
  created_at: string;
  last_login?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

export interface AuthResponse {
  user: AuthUser;
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

class AuthApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_AUTH_API_URL || 'http://localhost:8009';
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `Authentication failed: ${response.status}`);
    }

    return response.json();
  }

  async login(credentials: LoginRequest): Promise<AuthResponse> {
    return this.request<AuthResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  async register(userData: RegisterRequest): Promise<AuthResponse> {
    return this.request<AuthResponse>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async logout(token: string): Promise<void> {
    return this.request<void>('/api/auth/logout', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  }

  async refreshToken(refreshToken: string): Promise<{
    access_token: string;
    expires_in: number;
  }> {
    return this.request('/api/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  }

  async getCurrentUser(token: string): Promise<AuthUser> {
    return this.request<AuthUser>('/api/auth/me', {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  }

  async updateProfile(token: string, updates: Partial<AuthUser>): Promise<AuthUser> {
    return this.request<AuthUser>('/api/auth/profile', {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(updates),
    });
  }

  async changePassword(token: string, oldPassword: string, newPassword: string): Promise<void> {
    return this.request<void>('/api/auth/change-password', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        old_password: oldPassword,
        new_password: newPassword,
      }),
    });
  }
}

export const authApi = new AuthApiService();

// Consolidated API object for easy access
export const api = {
  auth: authApi,
  strategy: strategyApi,
  marketData: marketDataApi,
  riskManagement: riskManagementApi,
  noCode: noCodeApiClient,
} as const;