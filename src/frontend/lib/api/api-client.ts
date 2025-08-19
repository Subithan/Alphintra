// Central API client configuration for customer support integration
// This handles authentication, error handling, and common request logic

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

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
  private axiosInstance: AxiosInstance;

  constructor(config: Partial<ApiConfig> = {}) {
    this.config = {
      baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8080',
      timeout: 30000, // 30 seconds
      retries: 3,
      ...config,
    };

    // Create axios instance with enhanced configuration
    this.axiosInstance = axios.create({
      baseURL: this.config.baseUrl,
      timeout: this.config.timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.axiosInstance.interceptors.request.use(
      (config) => {
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        // Add request timestamp for monitoring
        config.metadata = { requestStartTime: Date.now() };
        
        return config;
      },
      (error) => {
        return Promise.reject(this.handleError(error));
      }
    );

    // Response interceptor
    this.axiosInstance.interceptors.response.use(
      (response: AxiosResponse) => {
        // Log response time for monitoring
        const requestStartTime = response.config.metadata?.requestStartTime;
        if (requestStartTime) {
          const responseTime = Date.now() - requestStartTime;
          console.debug(`API Response: ${response.config.method?.toUpperCase()} ${response.config.url} - ${responseTime}ms`);
        }
        
        return response;
      },
      (error) => {
        return Promise.reject(this.handleError(error));
      }
    );
  }

  private getAuthToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token') || this.config.authToken || null;
    }
    return this.config.authToken || null;
  }

  private handleError(error: any): ApiError {
    console.error('API Error:', error);

    if (error.response) {
      const { status, data } = error.response;
      
      // Handle specific HTTP status codes
      switch (status) {
        case 401:
          this.handleUnauthorized();
          return new ApiError(status, 'Authentication required', data);
        case 403:
          return new ApiError(status, 'Access forbidden', data);
        case 404:
          return new ApiError(status, 'Resource not found', data);
        case 422:
          return new ApiError(status, 'Validation failed', data);
        case 429:
          return new ApiError(status, 'Rate limit exceeded', data);
        case 500:
          return new ApiError(status, 'Internal server error', data);
        default:
          return new ApiError(status, data.message || 'API error occurred', data);
      }
    } else if (error.request) {
      return new ApiError(0, 'Network error', { message: 'No response received' });
    } else {
      return new ApiError(0, 'Request error', { message: error.message });
    }
  }

  private handleUnauthorized(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
  }

  // HTTP Methods using axios
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.get<T>(url, config);
    return response.data;
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.post<T>(url, data, config);
    return response.data;
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.put<T>(url, data, config);
    return response.data;
  }

  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.patch<T>(url, data, config);
    return response.data;
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.delete<T>(url, config);
    return response.data;
  }

  // Legacy fetch-based method for backward compatibility
  protected async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const config: AxiosRequestConfig = {
      method: (options.method as any) || 'GET',
      data: options.body ? JSON.parse(options.body as string) : undefined,
      headers: options.headers as any,
    };

    const response = await this.axiosInstance.request({
      url: endpoint,
      ...config,
    });

    return response.data;
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
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  }

  clearAuthToken(): void {
    this.config.authToken = undefined;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
  }

  // File upload helper
  async uploadFile<T = any>(url: string, file: File, onProgress?: (progress: number) => void): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    const config: AxiosRequestConfig = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    };

    const response = await this.axiosInstance.post<T>(url, formData, config);
    return response.data;
  }

  // Download helper
  async downloadFile(url: string, filename?: string): Promise<Blob> {
    const response = await this.axiosInstance.get(url, {
      responseType: 'blob',
    });

    // Create download link
    if (typeof window !== 'undefined') {
      const blob = new Blob([response.data]);
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename || 'download';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    }

    return response.data;
  }

  // Health check
  async healthCheck(): Promise<{
    status: 'healthy' | 'unhealthy';
    timestamp: string;
    services: Record<string, 'up' | 'down'>;
  }> {
    return this.get('/actuator/health');
  }

  // Get base URL
  getBaseURL(): string {
    return this.config.baseUrl;
  }
}

// Create and export singleton instance for customer support
export const apiClient = new BaseApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8080'
});

export { BaseApiClient };
export default apiClient;