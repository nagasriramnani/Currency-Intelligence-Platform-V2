/**
 * Alerts API Client
 * 
 * TypeScript client for the Intelligent Alerting System.
 * Handles all alert-related backend communication.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ============================================================================
// Types
// ============================================================================

export type AlertSeverity = 'info' | 'warning' | 'critical';
export type AlertState = 'open' | 'acknowledged' | 'resolved' | 'snoozed';
export type AlertType =
    | 'volatility_spike'
    | 'var_breach'
    | 'cvar_breach'
    | 'forecast_reversal'
    | 'model_confidence_drop'
    | 'regime_change'
    | 'correlation_shift'
    | 'portfolio_impact'
    | 'anomaly_detected'
    | 'threshold_breach';

export interface AlertContext {
    interpretation: string;
    business_impact: string;
    model_rationale: string;
    key_drivers: string[];
    uncertainty_change: string;
}

export interface SuggestedAction {
    action_type: 'hedge' | 'monitor' | 'no_action' | 'escalate';
    description: string;
    urgency: 'immediate' | 'today' | 'this_week' | 'none';
    instruments: string[];
    coverage_suggestion: number;
}

export interface PortfolioContext {
    currency: string;
    exposure_amount: number;
    exposure_direction: 'long' | 'short';
    estimated_impact: number;
    natural_hedges: string[];
    hedge_efficiency: number;
}

export interface IntelligentAlert {
    alert_id: string;
    alert_type: AlertType;
    severity: AlertSeverity;
    currency: string;
    created_at: string;
    expires_at: string | null;
    title: string;
    message: string;
    metrics: Record<string, number | string>;
    context: AlertContext | null;
    suggested_action: SuggestedAction | null;
    portfolio_context: PortfolioContext | null;
    model_name: string;
    model_confidence: number;
    state: AlertState;
    dedup_key: string;
    occurrence_count: number;
}

export interface TriggerResponse {
    status: 'triggered' | 'suppressed' | 'no_alert' | 'no_change';
    alert?: IntelligentAlert;
    sent_to_slack?: boolean;
    reason?: string;
    current_regime?: string;
    confidence?: number;
}

export interface AlertsResponse {
    alerts: IntelligentAlert[];
    count: number;
}

// ============================================================================
// Helper Functions
// ============================================================================

export const getSeverityColor = (severity: AlertSeverity): string => {
    switch (severity) {
        case 'critical': return 'rose';
        case 'warning': return 'amber';
        case 'info': return 'emerald';
        default: return 'sapphire';
    }
};

export const getSeverityEmoji = (severity: AlertSeverity): string => {
    switch (severity) {
        case 'critical': return '🔴';
        case 'warning': return '⚠️';
        case 'info': return 'ℹ️';
        default: return '📢';
    }
};

export const getAlertTypeLabel = (type: AlertType): string => {
    const labels: Record<AlertType, string> = {
        volatility_spike: 'Volatility Spike',
        var_breach: 'VaR Breach',
        cvar_breach: 'CVaR Breach',
        forecast_reversal: 'Forecast Reversal',
        model_confidence_drop: 'Confidence Drop',
        regime_change: 'Regime Change',
        correlation_shift: 'Correlation Shift',
        portfolio_impact: 'Portfolio Impact',
        anomaly_detected: 'Anomaly Detected',
        threshold_breach: 'Threshold Breach',
    };
    return labels[type] || type;
};

export const getUrgencyColor = (urgency: string): string => {
    switch (urgency) {
        case 'immediate': return 'rose';
        case 'today': return 'amber';
        case 'this_week': return 'blue';
        default: return 'slate';
    }
};

// ============================================================================
// API Client
// ============================================================================

class AlertsApiClient {
    private baseUrl: string;

    constructor(baseUrl: string = API_BASE_URL) {
        this.baseUrl = baseUrl;
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
            const text = await response.text();
            throw new Error(`API Error: ${response.status} - ${text}`);
        }

        return response.json();
    }

    // Get active alerts
    async getActiveAlerts(currency?: string): Promise<AlertsResponse> {
        const params = currency ? `?currency=${currency}` : '';
        return this.fetch<AlertsResponse>(`/api/alerts/active${params}`);
    }

    // Trigger volatility check
    async triggerVolatility(currency: string = 'EUR'): Promise<TriggerResponse> {
        return this.fetch<TriggerResponse>(`/api/alerts/trigger/volatility?currency=${currency}`, {
            method: 'POST',
        });
    }

    // Trigger VaR check
    async triggerVaR(currency: string = 'EUR', confidence: number = 0.95): Promise<TriggerResponse> {
        return this.fetch<TriggerResponse>(
            `/api/alerts/trigger/var?currency=${currency}&confidence=${confidence}`,
            { method: 'POST' }
        );
    }

    // Trigger regime check
    async triggerRegime(currency: string = 'EUR'): Promise<TriggerResponse> {
        return this.fetch<TriggerResponse>(`/api/alerts/trigger/regime?currency=${currency}`, {
            method: 'POST',
        });
    }

    // Acknowledge alert
    async acknowledgeAlert(alertId: string, user: string = 'web_user'): Promise<{ status: string }> {
        return this.fetch(`/api/alerts/${alertId}/acknowledge?user=${user}`, {
            method: 'POST',
        });
    }

    // Resolve alert
    async resolveAlert(alertId: string): Promise<{ status: string }> {
        return this.fetch(`/api/alerts/${alertId}/resolve`, {
            method: 'POST',
        });
    }

    // Snooze alert
    async snoozeAlert(alertId: string, hours: number = 4): Promise<{ status: string }> {
        return this.fetch(`/api/alerts/${alertId}/snooze?hours=${hours}`, {
            method: 'POST',
        });
    }

    // Send daily summary
    async sendSummary(): Promise<{ status: string }> {
        return this.fetch('/api/alerts/summary', {
            method: 'POST',
        });
    }

    // Update portfolio exposure
    async setPortfolioExposure(
        currency: string,
        amount: number,
        direction: 'long' | 'short' = 'long'
    ): Promise<{ status: string }> {
        return this.fetch(
            `/api/alerts/portfolio?currency=${currency}&amount=${amount}&direction=${direction}`,
            { method: 'POST' }
        );
    }
}

export const alertsApi = new AlertsApiClient();
