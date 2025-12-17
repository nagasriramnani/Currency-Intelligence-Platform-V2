/**
 * AlertCard Component
 * 
 * Displays an intelligent alert with severity badge, metrics, context,
 * suggested actions, and action buttons.
 */

'use client';

import React, { useState } from 'react';
import {
    AlertTriangle,
    AlertCircle,
    Info,
    TrendingUp,
    TrendingDown,
    Activity,
    Shield,
    Zap,
    CheckCircle,
    Clock,
    XCircle,
    ChevronDown,
    ChevronUp,
    Eye,
} from 'lucide-react';
import type {
    IntelligentAlert,
    AlertSeverity,
    AlertType,
} from '@/lib/alerts';
import {
    getSeverityColor,
    getAlertTypeLabel,
    getUrgencyColor,
} from '@/lib/alerts';

interface AlertCardProps {
    alert: IntelligentAlert;
    onAcknowledge?: (alertId: string) => void;
    onResolve?: (alertId: string) => void;
    onSnooze?: (alertId: string, hours: number) => void;
    onViewDetails?: (alert: IntelligentAlert) => void;
    isLoading?: boolean;
}

export function AlertCard({
    alert,
    onAcknowledge,
    onResolve,
    onSnooze,
    onViewDetails,
    isLoading,
}: AlertCardProps) {
    const [expanded, setExpanded] = useState(false);
    const [showSnoozeMenu, setShowSnoozeMenu] = useState(false);

    const severityColor = getSeverityColor(alert.severity);
    const typeLabel = getAlertTypeLabel(alert.alert_type);

    const getSeverityIcon = () => {
        switch (alert.severity) {
            case 'critical':
                return <AlertTriangle className="h-5 w-5" />;
            case 'warning':
                return <AlertCircle className="h-5 w-5" />;
            case 'info':
                return <Info className="h-5 w-5" />;
            default:
                return <AlertCircle className="h-5 w-5" />;
        }
    };

    const getAlertTypeIcon = () => {
        switch (alert.alert_type) {
            case 'volatility_spike':
                return <Activity className="h-4 w-4" />;
            case 'var_breach':
            case 'cvar_breach':
                return <Shield className="h-4 w-4" />;
            case 'regime_change':
                return <Zap className="h-4 w-4" />;
            case 'forecast_reversal':
                return <TrendingDown className="h-4 w-4" />;
            default:
                return <AlertCircle className="h-4 w-4" />;
        }
    };

    const severityStyles: Record<AlertSeverity, string> = {
        critical: 'border-rose-500/30 bg-rose-500/5',
        warning: 'border-amber-500/30 bg-amber-500/5',
        info: 'border-emerald-500/30 bg-emerald-500/5',
    };

    const severityBadgeStyles: Record<AlertSeverity, string> = {
        critical: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
        warning: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
        info: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    };

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    return (
        <div
            className={`rounded-xl border transition-all duration-200 ${severityStyles[alert.severity]} ${isLoading ? 'opacity-50' : ''
                }`}
        >
            {/* Header */}
            <div className="p-4">
                <div className="flex items-start justify-between gap-3">
                    {/* Severity Icon */}
                    <div
                        className={`rounded-lg p-2 ${severityBadgeStyles[alert.severity]}`}
                    >
                        {getSeverityIcon()}
                    </div>

                    {/* Main Content */}
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                            {/* Severity Badge */}
                            <span
                                className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${severityBadgeStyles[alert.severity]}`}
                            >
                                {alert.severity}
                            </span>
                            {/* Type Badge */}
                            <span className="text-[10px] font-medium bg-sapphire-800/50 text-sapphire-300 px-2 py-0.5 rounded-full border border-sapphire-700/30">
                                {typeLabel}
                            </span>
                            {/* Currency */}
                            <span className="text-sm font-bold text-white">
                                {alert.currency}
                            </span>
                        </div>

                        {/* Title */}
                        <h4 className="text-sm font-semibold text-white mt-2">
                            {alert.title}
                        </h4>

                        {/* Message */}
                        <p className="text-xs text-sapphire-300 mt-1 line-clamp-2">
                            {alert.message.replace(/\*/g, '')}
                        </p>

                        {/* Model Confidence */}
                        {alert.model_confidence > 0 && (
                            <div className="flex items-center gap-2 mt-2">
                                <span className="text-[10px] text-sapphire-400">Model Confidence:</span>
                                <div className="flex-1 max-w-[100px] h-1.5 bg-sapphire-800/50 rounded-full overflow-hidden">
                                    <div
                                        className={`h-full rounded-full ${alert.model_confidence > 0.8
                                                ? 'bg-emerald-500'
                                                : alert.model_confidence > 0.6
                                                    ? 'bg-amber-500'
                                                    : 'bg-rose-500'
                                            }`}
                                        style={{ width: `${alert.model_confidence * 100}%` }}
                                    />
                                </div>
                                <span className="text-[10px] font-mono text-sapphire-300">
                                    {Math.round(alert.model_confidence * 100)}%
                                </span>
                            </div>
                        )}
                    </div>

                    {/* Timestamp */}
                    <span className="text-[10px] text-sapphire-400 font-mono whitespace-nowrap">
                        {formatDate(alert.created_at)}
                    </span>
                </div>

                {/* Metrics Row */}
                {alert.metrics && Object.keys(alert.metrics).length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-3">
                        {Object.entries(alert.metrics)
                            .filter(([key]) => !key.includes('_'))
                            .slice(0, 4)
                            .map(([key, value]) => (
                                <span
                                    key={key}
                                    className="text-[10px] bg-sapphire-950/50 border border-sapphire-800/50 px-2 py-1 rounded-md"
                                >
                                    <span className="text-sapphire-500 uppercase tracking-wider">
                                        {key}:
                                    </span>{' '}
                                    <span className="text-sapphire-200 font-medium">
                                        {typeof value === 'number' ? value.toFixed(2) : String(value)}
                                    </span>
                                </span>
                            ))}
                    </div>
                )}

                {/* Expand/Collapse */}
                <button
                    onClick={() => setExpanded(!expanded)}
                    className="flex items-center gap-1 text-[10px] text-sapphire-400 hover:text-sapphire-300 mt-3"
                >
                    {expanded ? (
                        <>
                            <ChevronUp className="h-3 w-3" /> Less details
                        </>
                    ) : (
                        <>
                            <ChevronDown className="h-3 w-3" /> More details
                        </>
                    )}
                </button>
            </div>

            {/* Expanded Content */}
            {expanded && (
                <div className="px-4 pb-4 space-y-3 border-t border-sapphire-800/30 pt-3">
                    {/* Context */}
                    {alert.context && (
                        <div>
                            <h5 className="text-[10px] font-bold uppercase tracking-wider text-sapphire-400 mb-1">
                                Why This Matters
                            </h5>
                            <p className="text-xs text-sapphire-200">
                                {alert.context.interpretation}
                            </p>
                            {alert.context.business_impact && (
                                <p className="text-xs text-amber-300/80 mt-1">
                                    💰 {alert.context.business_impact}
                                </p>
                            )}
                        </div>
                    )}

                    {/* Suggested Action */}
                    {alert.suggested_action && (
                        <div>
                            <h5 className="text-[10px] font-bold uppercase tracking-wider text-sapphire-400 mb-1">
                                Suggested Action
                            </h5>
                            <div className="flex items-center gap-2">
                                <span
                                    className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-${getUrgencyColor(
                                        alert.suggested_action.urgency
                                    )}-500/20 text-${getUrgencyColor(alert.suggested_action.urgency)}-400 border border-${getUrgencyColor(alert.suggested_action.urgency)}-500/30`}
                                >
                                    {alert.suggested_action.urgency}
                                </span>
                                <span className="text-xs text-sapphire-200">
                                    {alert.suggested_action.action_type.toUpperCase()}:{' '}
                                    {alert.suggested_action.description}
                                </span>
                            </div>
                            {alert.suggested_action.coverage_suggestion > 0 && (
                                <p className="text-xs text-emerald-400 mt-1">
                                    📊 Suggested coverage: {Math.round(alert.suggested_action.coverage_suggestion * 100)}%
                                </p>
                            )}
                        </div>
                    )}

                    {/* Portfolio Context */}
                    {alert.portfolio_context && (
                        <div>
                            <h5 className="text-[10px] font-bold uppercase tracking-wider text-sapphire-400 mb-1">
                                Portfolio Impact
                            </h5>
                            <div className="flex flex-wrap gap-2 text-xs">
                                <span className="text-sapphire-200">
                                    {alert.portfolio_context.exposure_direction === 'long' ? '📈' : '📉'}{' '}
                                    ${alert.portfolio_context.exposure_amount.toLocaleString()} {alert.portfolio_context.exposure_direction}
                                </span>
                                {alert.portfolio_context.estimated_impact !== 0 && (
                                    <span
                                        className={
                                            alert.portfolio_context.estimated_impact < 0
                                                ? 'text-rose-400'
                                                : 'text-emerald-400'
                                        }
                                    >
                                        Impact: ${alert.portfolio_context.estimated_impact.toLocaleString()}
                                    </span>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Actions */}
            <div className="flex items-center gap-2 px-4 pb-4">
                {onAcknowledge && alert.state === 'open' && (
                    <button
                        onClick={() => onAcknowledge(alert.alert_id)}
                        disabled={isLoading}
                        className="flex items-center gap-1 text-[10px] font-medium px-3 py-1.5 rounded-lg bg-sapphire-600 text-white hover:bg-sapphire-500 disabled:opacity-50 transition-colors"
                    >
                        <CheckCircle className="h-3 w-3" />
                        Acknowledge
                    </button>
                )}

                {onResolve && (
                    <button
                        onClick={() => onResolve(alert.alert_id)}
                        disabled={isLoading}
                        className="flex items-center gap-1 text-[10px] font-medium px-3 py-1.5 rounded-lg bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-50 transition-colors"
                    >
                        <XCircle className="h-3 w-3" />
                        Resolve
                    </button>
                )}

                {onSnooze && (
                    <div className="relative">
                        <button
                            onClick={() => setShowSnoozeMenu(!showSnoozeMenu)}
                            disabled={isLoading}
                            className="flex items-center gap-1 text-[10px] font-medium px-3 py-1.5 rounded-lg bg-sapphire-800/50 text-sapphire-300 hover:bg-sapphire-700/50 disabled:opacity-50 transition-colors border border-sapphire-700/30"
                        >
                            <Clock className="h-3 w-3" />
                            Snooze
                            <ChevronDown className="h-3 w-3" />
                        </button>

                        {showSnoozeMenu && (
                            <div className="absolute top-full left-0 mt-1 bg-sapphire-900 border border-sapphire-700/50 rounded-lg shadow-lg z-10 py-1 min-w-[100px]">
                                {[1, 4, 24].map((hours) => (
                                    <button
                                        key={hours}
                                        onClick={() => {
                                            onSnooze(alert.alert_id, hours);
                                            setShowSnoozeMenu(false);
                                        }}
                                        className="w-full text-left px-3 py-1.5 text-xs text-sapphire-200 hover:bg-sapphire-800/50"
                                    >
                                        {hours}h
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {onViewDetails && (
                    <button
                        onClick={() => onViewDetails(alert)}
                        className="flex items-center gap-1 text-[10px] font-medium px-3 py-1.5 rounded-lg bg-sapphire-800/30 text-sapphire-300 hover:bg-sapphire-700/30 transition-colors border border-sapphire-700/30 ml-auto"
                    >
                        <Eye className="h-3 w-3" />
                        Details
                    </button>
                )}
            </div>
        </div>
    );
}

export default AlertCard;
