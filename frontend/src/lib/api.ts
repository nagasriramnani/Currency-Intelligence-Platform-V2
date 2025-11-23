/**
 * API Client for Currency Intelligence Platform
 * Handles all backend communication
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface LatestRate {
  currency: string;
  pair: string;
  latest_rate: number;
  latest_date: string;
  mom_change: number | null;
  qoq_change: number | null;
  yoy_change: number | null;
  direction: 'Rising' | 'Falling' | 'Flat';
  fmp_available?: boolean;
}

export interface TimeSeriesDataPoint {
  record_date: string;
  currency: string;
  pair: string;
  exchange_rate: number;
  returns: number | null;
  rolling_volatility: number | null;
  mom_change: number | null;
  yoy_change: number | null;
}

export interface VolatilityMetrics {
  currency: string;
  pair: string;
  current_volatility: number | null;
  annualized_volatility: number | null;
  mean_volatility: number | null;
  volatility_regime: string;
}

export interface ForecastPoint {
  date: string;
  value: number;
}

export interface ConfidenceBandPoint {
  date: string;
  lower: number;
  upper: number;
}

export interface ForecastData {
  currency: string;
  forecast_start: string | null;
  historical: ForecastPoint[];
  forecast: ForecastPoint[];
  confidence?: ConfidenceBandPoint[];
  insight?: string | null;
}

export interface Insight {
  currency: string;
  insights: string[];
}

export interface YoYComparison {
  currency: string;
  pair: string;
  current_rate: number;
  year_ago_rate: number | null;
  yoy_change_pct: number | null;
  current_date: string;
}

export interface Anomaly {
  record_date: string;
  currency: string;
  exchange_rate: number;
  returns: number | null;
}

export interface AlertHistory {
  timestamp: string;
  trigger_type: string;
  currency: string;
  details: Record<string, any>;
}

export interface HighlightItem {
  title: string;
  body: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private buildQuery(params: Record<string, string | undefined | null>) {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value) {
        query.append(key, value);
      }
    });
    const queryString = query.toString();
    return queryString ? `?${queryString}` : '';
  }

  private async fetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  // Health check
  async healthCheck() {
    return this.fetch('/');
  }

  // Data endpoints
  async getTimeSeriesData(
    currencies?: string[],
    startDate?: string,
    endDate?: string
  ): Promise<{ data: TimeSeriesDataPoint[]; count: number }> {
    const params = new URLSearchParams();
    if (currencies && currencies.length > 0) {
      params.append('currencies', currencies.join(','));
    }
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const query = params.toString() ? `?${params.toString()}` : '';
    return this.fetch(`/api/data/timeseries${query}`);
  }

  async refreshData(daysBack: number = 1460): Promise<{ status: string; message: string }> {
    return this.fetch(`/api/data/refresh?days_back=${daysBack}`, {
      method: 'POST',
    });
  }

  // Metrics endpoints
  async getLatestRates(startDate?: string, endDate?: string): Promise<LatestRate[]> {
    const query = this.buildQuery({
      start_date: startDate ?? null,
      end_date: endDate ?? null,
    });
    return this.fetch(`/api/metrics/latest${query}`);
  }

  async getYoYComparison(startDate?: string, endDate?: string): Promise<{ data: YoYComparison[] }> {
    const query = this.buildQuery({
      start_date: startDate ?? null,
      end_date: endDate ?? null,
    });
    return this.fetch(`/api/metrics/yoy-comparison${query}`);
  }

  // Volatility endpoints
  async getVolatilitySummary(): Promise<VolatilityMetrics[]> {
    return this.fetch('/api/volatility/summary');
  }

  async getVolatilityTimeSeries(
    currency: string
  ): Promise<{ currency: string; data: any[] }> {
    return this.fetch(`/api/volatility/${currency}`);
  }

  // Forecast endpoints
  async getForecast(
    currency: string,
    horizon: number = 6,
    startDate?: string,
    endDate?: string
  ): Promise<ForecastData> {
    const params = new URLSearchParams({ horizon: String(horizon) });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    return this.fetch(`/api/forecast/${currency}?${params.toString()}`);
  }

  // Anomaly endpoints
  async getAnomalies(
    currency?: string,
    startDate?: string,
    endDate?: string
  ): Promise<{ anomalies: Anomaly[]; count?: number }> {
    const params = new URLSearchParams();
    if (currency) params.append('currency', currency);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    const query = params.toString() ? `?${params.toString()}` : '';
    return this.fetch(`/api/anomalies${query}`);
  }

  // Insights endpoints
  async getInsights(currency: string): Promise<Insight> {
    return this.fetch(`/api/insights/${currency}`);
  }

  async getSummaryInsight(): Promise<{ summary: string }> {
    return this.fetch('/api/insights/summary');
  }

  async getHighlights(startDate?: string, endDate?: string): Promise<{ highlights: HighlightItem[] }> {
    const query = this.buildQuery({
      start_date: startDate ?? null,
      end_date: endDate ?? null,
    });
    return this.fetch(`/api/insights/highlights${query}`);
  }

  // Alert endpoints
  async sendTestAlert(): Promise<{ success: boolean; message: string }> {
    return this.fetch('/api/alerts/test', {
      method: 'POST',
    });
  }

  async getAlertHistory(limit: number = 10): Promise<{ alerts: AlertHistory[]; count: number }> {
    return this.fetch(`/api/alerts/history?limit=${limit}`);
  }

  async checkAlerts(): Promise<{ alerts_sent: any[]; count: number }> {
    return this.fetch('/api/alerts/check', {
      method: 'POST',
    });
  }

  async sendSlackSummary(payload: { start_date?: string | null; end_date?: string | null }) {
    return this.fetch('/api/alerts/slack-summary', {
      method: 'POST',
      body: JSON.stringify(payload ?? {}),
    });
  }
}

export const apiClient = new ApiClient();

