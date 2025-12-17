/**
 * Intelligent Alerts Panel Component
 * 
 * Displays intelligent alerts with severity badges, metrics, context,
 * and action buttons. Includes trigger buttons to generate alerts.
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
    Bell,
    AlertTriangle,
    Activity,
    Shield,
    Zap,
    RefreshCw,
    CheckCircle,
    XCircle,
    Loader2,
} from 'lucide-react';
import AlertCard from '@/components/AlertCard';
import { SkeletonBlock } from '@/components/SkeletonBlock';
import {
    alertsApi,
    type IntelligentAlert,
    type TriggerResponse,
} from '@/lib/alerts';

interface IntelligentAlertsPanelProps {
    onSendSummary?: () => void;
    sendSummaryLoading?: boolean;
    summaryStatus?: 'success' | 'error';
}

export function IntelligentAlertsPanel({
    onSendSummary,
    sendSummaryLoading,
    summaryStatus,
}: IntelligentAlertsPanelProps) {
    const [alerts, setAlerts] = useState<IntelligentAlert[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [actionLoading, setActionLoading] = useState<string | null>(null);

    // Trigger button states
    const [triggerLoading, setTriggerLoading] = useState<string | null>(null);
    const [lastTriggerResult, setLastTriggerResult] = useState<{
        type: string;
        status: string;
    } | null>(null);

    // Fetch alerts
    const fetchAlerts = useCallback(async () => {
        try {
            const response = await alertsApi.getActiveAlerts();
            setAlerts(response.alerts || []);
        } catch (error) {
            console.error('Failed to fetch alerts:', error);
        } finally {
            setIsLoading(false);
            setIsRefreshing(false);
        }
    }, []);

    // Initial fetch and polling
    useEffect(() => {
        fetchAlerts();

        // Poll every 30 seconds
        const interval = setInterval(fetchAlerts, 30000);
        return () => clearInterval(interval);
    }, [fetchAlerts]);

    // Refresh alerts
    const handleRefresh = async () => {
        setIsRefreshing(true);
        await fetchAlerts();
    };

    // Trigger volatility check
    const handleTriggerVolatility = async () => {
        setTriggerLoading('volatility');
        try {
            const result = await alertsApi.triggerVolatility('EUR');
            setLastTriggerResult({ type: 'Volatility', status: result.status });
            await fetchAlerts();
        } catch (error) {
            console.error('Trigger failed:', error);
            setLastTriggerResult({ type: 'Volatility', status: 'error' });
        } finally {
            setTriggerLoading(null);
            setTimeout(() => setLastTriggerResult(null), 3000);
        }
    };

    // Trigger VaR check
    const handleTriggerVaR = async () => {
        setTriggerLoading('var');
        try {
            const result = await alertsApi.triggerVaR('EUR');
            setLastTriggerResult({ type: 'VaR', status: result.status });
            await fetchAlerts();
        } catch (error) {
            console.error('Trigger failed:', error);
            setLastTriggerResult({ type: 'VaR', status: 'error' });
        } finally {
            setTriggerLoading(null);
            setTimeout(() => setLastTriggerResult(null), 3000);
        }
    };

    // Trigger regime check
    const handleTriggerRegime = async () => {
        setTriggerLoading('regime');
        try {
            const result = await alertsApi.triggerRegime('EUR');
            setLastTriggerResult({ type: 'Regime', status: result.status });
            await fetchAlerts();
        } catch (error) {
            console.error('Trigger failed:', error);
            setLastTriggerResult({ type: 'Regime', status: 'error' });
        } finally {
            setTriggerLoading(null);
            setTimeout(() => setLastTriggerResult(null), 3000);
        }
    };

    // Handle acknowledge
    const handleAcknowledge = async (alertId: string) => {
        setActionLoading(alertId);
        try {
            await alertsApi.acknowledgeAlert(alertId);
            await fetchAlerts();
        } catch (error) {
            console.error('Acknowledge failed:', error);
        } finally {
            setActionLoading(null);
        }
    };

    // Handle resolve
    const handleResolve = async (alertId: string) => {
        setActionLoading(alertId);
        try {
            await alertsApi.resolveAlert(alertId);
            await fetchAlerts();
        } catch (error) {
            console.error('Resolve failed:', error);
        } finally {
            setActionLoading(null);
        }
    };

    // Handle snooze
    const handleSnooze = async (alertId: string, hours: number) => {
        setActionLoading(alertId);
        try {
            await alertsApi.snoozeAlert(alertId, hours);
            await fetchAlerts();
        } catch (error) {
            console.error('Snooze failed:', error);
        } finally {
            setActionLoading(null);
        }
    };

    const getStatusBadge = () => {
        if (!lastTriggerResult) return null;

        const isSuccess = ['triggered', 'no_alert', 'no_change'].includes(lastTriggerResult.status);

        return (
            <span
                className={`flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded-full border ${isSuccess
                        ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
                        : 'text-rose-400 bg-rose-500/10 border-rose-500/20'
                    }`}
            >
                {isSuccess ? <CheckCircle className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                {lastTriggerResult.type}: {lastTriggerResult.status}
            </span>
        );
    };

    return (
        <div className="glass-panel rounded-2xl p-6 h-full">
            {/* Header */}
            <div className="flex flex-col gap-4 pb-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Bell className="h-5 w-5 text-sapphire-400" />
                        <h3 className="text-lg font-bold text-white">Recent Alerts</h3>
                        {alerts.length > 0 && (
                            <span className="text-xs bg-sapphire-600/30 text-sapphire-300 px-2 py-0.5 rounded-full border border-sapphire-600/30">
                                {alerts.length}
                            </span>
                        )}
                    </div>

                    <div className="flex items-center gap-2">
                        {getStatusBadge()}

                        {summaryStatus === 'success' && (
                            <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded-full border border-emerald-500/20">
                                <CheckCircle className="h-3 w-3" /> Sent to Slack
                            </span>
                        )}

                        <button
                            onClick={handleRefresh}
                            disabled={isRefreshing}
                            className="p-1.5 rounded-lg text-sapphire-400 hover:text-sapphire-300 hover:bg-sapphire-800/30 disabled:opacity-50 transition-colors"
                        >
                            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                        </button>
                    </div>
                </div>

                {/* Trigger Buttons */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    <button
                        onClick={handleTriggerVolatility}
                        disabled={!!triggerLoading}
                        className="flex items-center justify-center gap-1.5 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs font-medium text-amber-400 hover:bg-amber-500/20 disabled:opacity-50 transition-all"
                    >
                        {triggerLoading === 'volatility' ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                            <Activity className="h-3.5 w-3.5" />
                        )}
                        Volatility Check
                    </button>

                    <button
                        onClick={handleTriggerVaR}
                        disabled={!!triggerLoading}
                        className="flex items-center justify-center gap-1.5 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs font-medium text-rose-400 hover:bg-rose-500/20 disabled:opacity-50 transition-all"
                    >
                        {triggerLoading === 'var' ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                            <Shield className="h-3.5 w-3.5" />
                        )}
                        VaR Check
                    </button>

                    <button
                        onClick={handleTriggerRegime}
                        disabled={!!triggerLoading}
                        className="flex items-center justify-center gap-1.5 rounded-lg border border-violet-500/30 bg-violet-500/10 px-3 py-2 text-xs font-medium text-violet-400 hover:bg-violet-500/20 disabled:opacity-50 transition-all"
                    >
                        {triggerLoading === 'regime' ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                            <Zap className="h-3.5 w-3.5" />
                        )}
                        Regime Check
                    </button>

                    {onSendSummary && (
                        <button
                            onClick={onSendSummary}
                            disabled={sendSummaryLoading}
                            className="flex items-center justify-center gap-1.5 rounded-lg bg-sapphire-600 px-3 py-2 text-xs font-semibold text-white hover:bg-sapphire-500 disabled:opacity-50 transition-all shadow-lg shadow-sapphire-600/20"
                        >
                            {sendSummaryLoading ? (
                                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            ) : null}
                            Send Summary
                        </button>
                    )}
                </div>
            </div>

            {/* Alerts List */}
            {isLoading ? (
                <div className="space-y-3">
                    {[1, 2, 3].map((i) => (
                        <SkeletonBlock key={i} className="h-32 bg-sapphire-800/50" />
                    ))}
                </div>
            ) : alerts.length === 0 ? (
                <div className="rounded-xl border border-dashed border-sapphire-700/30 bg-sapphire-900/20 px-4 py-12 text-center">
                    <Bell className="h-10 w-10 mx-auto mb-3 text-sapphire-600 opacity-50" />
                    <p className="text-sm text-sapphire-400 mb-2">No active alerts</p>
                    <p className="text-xs text-sapphire-500">
                        Click the trigger buttons above to check for alerts
                    </p>
                </div>
            ) : (
                <div className="space-y-3 max-h-[500px] overflow-y-auto custom-scrollbar pr-2">
                    {alerts.map((alert) => (
                        <AlertCard
                            key={alert.alert_id}
                            alert={alert}
                            onAcknowledge={handleAcknowledge}
                            onResolve={handleResolve}
                            onSnooze={handleSnooze}
                            isLoading={actionLoading === alert.alert_id}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}

export default IntelligentAlertsPanel;
