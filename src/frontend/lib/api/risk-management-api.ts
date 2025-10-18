// API service for risk management operations
// This replaces direct database access with proper API calls to backend services

export interface RiskProfile {
  id: string;
  name: string;
  description: string;
  max_position_size_percent: number;
  max_portfolio_risk_percent: number;
  max_daily_loss_percent: number;
  max_drawdown_percent: number;
  allowed_instruments: string[];
  blocked_instruments: string[];
  position_limits: PositionLimit[];
  risk_metrics: RiskMetrics;
  created_at: string;
  updated_at: string;
}

export interface PositionLimit {
  instrument_type: string;
  max_position_value: number;
  max_leverage: number;
  concentration_limit_percent: number;
}

export interface RiskMetrics {
  current_portfolio_risk: number;
  var_1d: number; // Value at Risk 1 day
  var_1w: number; // Value at Risk 1 week
  expected_shortfall: number;
  beta: number;
  correlation_matrix: Record<string, Record<string, number>>;
  stress_test_results: StressTestResult[];
}

export interface StressTestResult {
  scenario_name: string;
  portfolio_impact_percent: number;
  estimated_loss: number;
  probability: number;
}

export interface RiskAlert {
  id: string;
  type: 'position_limit' | 'portfolio_risk' | 'drawdown' | 'var_breach' | 'concentration';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  current_value: number;
  threshold_value: number;
  strategy_id?: string;
  symbol?: string;
  timestamp: string;
  acknowledged: boolean;
  resolved: boolean;
}

export interface PositionRiskAssessment {
  symbol: string;
  side: 'long' | 'short';
  quantity: number;
  entry_price: number;
  current_price: number;
  position_value: number;
  unrealized_pnl: number;
  risk_metrics: {
    position_risk_percent: number;
    portfolio_impact_percent: number;
    var_contribution: number;
    correlation_risk: number;
    liquidity_risk: 'low' | 'medium' | 'high';
  };
  risk_status: 'safe' | 'warning' | 'danger';
  recommendations: string[];
}

import { gatewayHttpBaseUrl } from '../config/gateway';
import { getToken } from '../auth';

class RiskManagementApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = gatewayHttpBaseUrl;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const base = this.baseUrl.replace(/\/+$/, '');
    const url = `${base}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    const token = getToken();
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      headers,
      ...options,
    });

    if (!response.ok) {
      throw new Error(`Risk Management API request failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Risk profile management
  async createRiskProfile(profile: Omit<RiskProfile, 'id' | 'created_at' | 'updated_at' | 'risk_metrics'>): Promise<RiskProfile> {
    return this.request<RiskProfile>('/api/risk-profiles', {
      method: 'POST',
      body: JSON.stringify(profile),
    });
  }

  async getRiskProfile(id: string): Promise<RiskProfile> {
    return this.request<RiskProfile>(`/api/risk-profiles/${id}`);
  }

  async updateRiskProfile(id: string, updates: Partial<RiskProfile>): Promise<RiskProfile> {
    return this.request<RiskProfile>(`/api/risk-profiles/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteRiskProfile(id: string): Promise<void> {
    return this.request<void>(`/api/risk-profiles/${id}`, {
      method: 'DELETE',
    });
  }

  async listRiskProfiles(): Promise<RiskProfile[]> {
    return this.request<RiskProfile[]>('/api/risk-profiles');
  }

  // Real-time risk monitoring
  async getCurrentPortfolioRisk(): Promise<{
    total_portfolio_value: number;
    total_risk_percent: number;
    var_1d: number;
    var_1w: number;
    max_drawdown: number;
    current_drawdown: number;
    position_count: number;
    concentration_risk: number;
    leverage_ratio: number;
    cash_available: number;
  }> {
    return this.request('/api/portfolio/risk');
  }

  async assessPositionRisk(params: {
    symbol: string;
    side: 'long' | 'short';
    quantity: number;
    price: number;
  }): Promise<PositionRiskAssessment> {
    return this.request<PositionRiskAssessment>('/api/positions/assess-risk', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  async validateTradeRisk(params: {
    symbol: string;
    side: 'long' | 'short';
    quantity: number;
    price: number;
    strategy_id?: string;
  }): Promise<{
    approved: boolean;
    risk_score: number;
    warnings: string[];
    rejections: string[];
    max_allowed_quantity?: number;
  }> {
    return this.request('/api/trades/validate-risk', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  // Risk alerts
  async getRiskAlerts(params?: {
    severity?: string;
    type?: string;
    unresolved_only?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<{
    alerts: RiskAlert[];
    total: number;
  }> {
    const searchParams = new URLSearchParams();
    if (params?.severity) searchParams.set('severity', params.severity);
    if (params?.type) searchParams.set('type', params.type);
    if (params?.unresolved_only) searchParams.set('unresolved_only', 'true');
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.offset) searchParams.set('offset', params.offset.toString());

    const queryString = searchParams.toString();
    const endpoint = `/api/alerts${queryString ? `?${queryString}` : ''}`;
    
    return this.request(endpoint);
  }

  async acknowledgeAlert(alertId: string): Promise<void> {
    return this.request<void>(`/api/alerts/${alertId}/acknowledge`, {
      method: 'POST',
    });
  }

  async resolveAlert(alertId: string, resolution_note?: string): Promise<void> {
    return this.request<void>(`/api/alerts/${alertId}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ resolution_note }),
    });
  }

  // Stress testing
  async runStressTest(params: {
    scenario_type: 'market_crash' | 'volatility_spike' | 'correlation_breakdown' | 'custom';
    parameters?: Record<string, number>;
    portfolio_snapshot?: boolean;
  }): Promise<{
    test_id: string;
    scenario_name: string;
    portfolio_impact_percent: number;
    estimated_loss: number;
    worst_positions: {
      symbol: string;
      impact_percent: number;
      estimated_loss: number;
    }[];
    recommendations: string[];
    started_at: string;
    completed_at: string;
  }> {
    return this.request('/api/stress-tests', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  async getStressTestResults(testId: string): Promise<any> {
    return this.request(`/api/stress-tests/${testId}`);
  }

  async listStressTests(limit?: number): Promise<any[]> {
    const endpoint = limit ? `/api/stress-tests?limit=${limit}` : '/api/stress-tests';
    return this.request(endpoint);
  }

  // Risk reporting
  async generateRiskReport(params: {
    start_date: string;
    end_date: string;
    include_stress_tests?: boolean;
    include_var_analysis?: boolean;
  }): Promise<{
    report_id: string;
    period: { start: string; end: string };
    summary: {
      avg_portfolio_risk: number;
      max_drawdown: number;
      var_breaches: number;
      total_alerts: number;
      stress_tests_run: number;
    };
    download_url: string;
    expires_at: string;
  }> {
    return this.request('/api/reports/risk', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  // Emergency controls
  async enableEmergencyStop(reason: string): Promise<void> {
    return this.request<void>('/api/emergency/stop', {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }

  async disableEmergencyStop(): Promise<void> {
    return this.request<void>('/api/emergency/stop', {
      method: 'DELETE',
    });
  }

  async getEmergencyStatus(): Promise<{
    emergency_stop_active: boolean;
    activated_at?: string;
    activated_by?: string;
    reason?: string;
  }> {
    return this.request('/api/emergency/status');
  }
}

// Export singleton instance
export const riskManagementApi = new RiskManagementApiService();
