/**
 * Trust Signals Component
 * 
 * Displays quiet credibility markers that reassure without drawing attention.
 * Used throughout the dashboard to show data freshness and model status.
 */

import React from 'react';
import { CheckCircle2, Clock, AlertTriangle, Database, RefreshCw } from 'lucide-react';

interface TrustSignalProps {
    type: 'success' | 'warning' | 'info';
    label: string;
    timestamp?: string;
    className?: string;
}

export function TrustSignal({ type, label, timestamp, className = '' }: TrustSignalProps) {
    const dotColors = {
        success: 'bg-emerald-500/80',
        warning: 'bg-amber-500/80',
        info: 'bg-sapphire-400/80'
    };

    return (
        <div className={`trust-signal ${className}`}>
            <span className={`trust-dot ${dotColors[type]}`} />
            <span>{label}</span>
            {timestamp && (
                <span className="text-sapphire-500">· {timestamp}</span>
            )}
        </div>
    );
}

interface DataFreshnessProps {
    lastUpdated: Date | string | null;
    className?: string;
}

export function DataFreshness({ lastUpdated, className = '' }: DataFreshnessProps) {
    if (!lastUpdated) {
        return (
            <TrustSignal
                type="warning"
                label="Data freshness unknown"
                className={className}
            />
        );
    }

    const date = lastUpdated instanceof Date ? lastUpdated : new Date(lastUpdated);
    const now = new Date();
    const diffMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));

    let timeAgo: string;
    let type: 'success' | 'warning' | 'info' = 'success';

    if (diffMinutes < 1) {
        timeAgo = 'just now';
    } else if (diffMinutes < 60) {
        timeAgo = `${diffMinutes}m ago`;
    } else if (diffMinutes < 1440) {
        const hours = Math.floor(diffMinutes / 60);
        timeAgo = `${hours}h ago`;
        type = hours > 6 ? 'warning' : 'info';
    } else {
        const days = Math.floor(diffMinutes / 1440);
        timeAgo = `${days}d ago`;
        type = 'warning';
    }

    return (
        <TrustSignal
            type={type}
            label="Last refreshed"
            timestamp={timeAgo}
            className={className}
        />
    );
}

interface ModelStatusProps {
    modelType?: string | null;
    trainedAt?: string | null;
    isFallback?: boolean;
    className?: string;
}

export function ModelStatus({ modelType, trainedAt, isFallback, className = '' }: ModelStatusProps) {
    if (!modelType) {
        return (
            <div className={`flex items-center gap-1.5 text-[10px] text-amber-400 ${className}`}>
                <AlertTriangle className="w-3 h-3" />
                <span>No model loaded</span>
            </div>
        );
    }

    if (isFallback) {
        return (
            <div className={`flex items-center gap-1.5 text-[10px] text-amber-400 ${className}`}>
                <AlertTriangle className="w-3 h-3" />
                <span>Fallback model in use</span>
            </div>
        );
    }

    let trainedAgo = '';
    if (trainedAt) {
        const date = new Date(trainedAt);
        const now = new Date();
        const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
        trainedAgo = diffDays === 0 ? 'today' : diffDays === 1 ? 'yesterday' : `${diffDays}d ago`;
    }

    return (
        <div className={`flex items-center gap-1.5 text-[10px] text-sapphire-400 ${className}`}>
            <CheckCircle2 className="w-3 h-3 text-emerald-500/80" />
            <span>Model trained {trainedAgo}</span>
            <span className="text-sapphire-600">·</span>
            <span className="uppercase">{modelType}</span>
        </div>
    );
}

interface DataSourceProps {
    source?: string;
    verified?: boolean;
    className?: string;
}

export function DataSource({ source = 'Treasury', verified = true, className = '' }: DataSourceProps) {
    return (
        <div className={`flex items-center gap-1.5 text-[10px] text-sapphire-400 ${className}`}>
            <Database className="w-3 h-3" />
            <span>{source}</span>
            {verified && (
                <>
                    <span className="text-sapphire-600">·</span>
                    <CheckCircle2 className="w-3 h-3 text-emerald-500/60" />
                    <span className="text-emerald-500/80">Verified</span>
                </>
            )}
        </div>
    );
}

// Combined trust footer for cards
interface TrustFooterProps {
    lastUpdated?: Date | string | null;
    modelType?: string | null;
    trainedAt?: string | null;
    isFallback?: boolean;
    source?: string;
    className?: string;
}

export function TrustFooter({
    lastUpdated,
    modelType,
    trainedAt,
    isFallback,
    source,
    className = ''
}: TrustFooterProps) {
    return (
        <div className={`flex flex-wrap items-center gap-x-4 gap-y-1 pt-3 mt-3 border-t border-sapphire-800/50 ${className}`}>
            {lastUpdated && <DataFreshness lastUpdated={lastUpdated} />}
            {modelType && <ModelStatus modelType={modelType} trainedAt={trainedAt} isFallback={isFallback} />}
            {source && <DataSource source={source} />}
        </div>
    );
}
