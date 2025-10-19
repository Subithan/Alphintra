// Central API client configuration
// This handles authentication, error handling, and common request logic

import { gatewayHttpBaseUrl } from '../config/gateway';
import { getToken } from '../auth';

export interface ApiConfig {
  baseUrl: string;
  timeout: number;
  retries: number;
  authToken?: string;
}

export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  errors?: string[];
  metadata?: {
    total?: number;
    page?: number;
    limit?: number;
    timestamp: string;
  };
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public response?: any
  ) {
    super(`API Error: ${status} ${statusText}`);
    this.name = 'ApiError';
  }
}

class BaseApiClient {
  protected config: ApiConfig;

  constructor(config: Partial<ApiConfig> = {}) {
    this.config = {
      baseUrl: gatewayHttpBaseUrl,
      timeout: 30000, // 30 seconds
      retries: 3,
      ...config,
    };
  }

  protected async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const base = this.config.baseUrl.replace(/\/+$/, '');
    const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = `${base}${path}`;
    const controller = new AbortController();
    
    // Set timeout
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

    try {
      const headers: Record<string, string> = {
        ...(options.headers as Record<string, string> || {}),
      };

      // Ensure Content-Type for JSON payloads unless explicitly provided
      if (!('Content-Type' in headers)) {
        headers['Content-Type'] = 'application/json';
      }

      // Resolve auth token (explicit config takes precedence over stored token)
      const runtimeToken =
        this.config.authToken ??
        getToken();

      if (runtimeToken && !headers['Authorization']) {
        headers['Authorization'] = `Bearer ${runtimeToken}`;
      }

      const debug = process.env.NEXT_PUBLIC_DEBUG_API === 'true';

      // Debug logging (without leaking full token)
      if (debug) {
        const authHeader = headers['Authorization'] || headers['authorization'];
        const masked = authHeader && authHeader.startsWith('Bearer ')
          ? `Bearer ${authHeader.slice(7, 11)}...`
          : authHeader ? '<custom auth header>' : '<none>';
        // eslint-disable-next-line no-console
        console.log('[ApiClient] Request', {
          url,
          method: options.method || 'GET',
          hasAuth: Boolean(authHeader),
          authPreview: masked,
        });
      }

      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (debug) {
        // eslint-disable-next-line no-console
        console.log('[ApiClient] Response', { url, status: response.status });
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(response.status, response.statusText, errorData);
      }

      const data = await response.json();
      
      // Handle wrapped API responses
      if (data.success !== undefined) {
        if (!data.success) {
          throw new Error(data.message || 'API request failed');
        }
        return data.data;
      }

      return data;
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof ApiError) {
        throw error;
      }

      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Request timeout');
      }

      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      throw new Error(`Network error: ${errorMessage}`);
    }
  }

  protected async requestWithRetry<T>(
    endpoint: string,
    options: RequestInit = {},
    retryCount = 0
  ): Promise<T> {
    try {
      return await this.request<T>(endpoint, options);
    } catch (error) {
      if (retryCount < this.config.retries && this.shouldRetry(error)) {
        // Exponential backoff
        const delay = Math.min(1000 * Math.pow(2, retryCount), 10000);
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.requestWithRetry<T>(endpoint, options, retryCount + 1);
      }
      throw error;
    }
  }

  private shouldRetry(error: any): boolean {
    // Retry on network errors or 5xx server errors
    if (error instanceof ApiError) {
      return error.status >= 500 && error.status < 600;
    }
    
    return error.message.includes('Network error') || 
           error.message.includes('Request timeout');
  }

  // Utility methods
  protected buildQueryString(params: Record<string, any>): string {
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach(item => searchParams.append(key, item.toString()));
        } else {
          searchParams.set(key, value.toString());
        }
      }
    });

    return searchParams.toString();
  }

  // Authentication methods
  setAuthToken(token: string): void {
    this.config.authToken = token;
  }

  clearAuthToken(): void {
    this.config.authToken = undefined;
  }

  // HTTP Methods
  async get<T>(endpoint: string): Promise<T> {
    return this.requestWithRetry<T>(endpoint, {
      method: 'GET',
    });
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.requestWithRetry<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.requestWithRetry<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async patch<T>(endpoint: string, data?: any): Promise<T> {
    return this.requestWithRetry<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.requestWithRetry<T>(endpoint, {
      method: 'DELETE',
    });
  }

  // Health check
  async healthCheck(): Promise<{
    status: 'healthy' | 'unhealthy';
    timestamp: string;
    services: Record<string, 'up' | 'down'>;
  }> {
    return this.request('/api/health');
  }
}

export { BaseApiClient };
