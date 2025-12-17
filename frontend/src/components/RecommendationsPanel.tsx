'use client';

import React from 'react';
import { ShieldCheck, AlertCircle, TrendingDown, Clock, Target } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Recommendation {
    currency: string;
    action: string;
    urgency: string;
    rationale: string;
    suggested_coverage: number;
    instruments: string[];
    confidence: number;
}

interface RecommendationsData {
    overall_risk_level: string;
    overall_recommendation: string;
    currency_recommendations: Recommendation[];
    cross_currency_opportunities: string[];
    estimated_risk_reduction: number;
}

interface RecommendationsPanelProps {
    data: RecommendationsData | null;
    isLoading?: boolean;
}

function getUrgencyStyle(urgency: string) {
    switch (urgency) {
        case 'immediate':
            return { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/50' };
        case 'soon':
            return { bg: 'bg-orange-500/20', text: 'text-orange-400', border: 'border-orange-500/50' };
        default:
            return { bg: 'bg-sapphire-500/20', text: 'text-sapphire-400', border: 'border-sapphire-500/50' };
    }
}

function getActionIcon(action: string) {
    switch (action) {
        case 'hedge':
            return ShieldCheck;
        case 'reduce':
            return TrendingDown;
        default:
            return Target;
    }
}

function getRiskLevelStyle(level: string) {
    switch (level) {
        case 'critical':
            return 'bg-red-500/20 text-red-400 border-red-500/50';
        case 'high':
            return 'bg-orange-500/20 text-orange-400 border-orange-500/50';
        case 'moderate':
            return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
        default:
            return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50';
    }
}

export function RecommendationsPanel({ data, isLoading }: RecommendationsPanelProps) {
    if (isLoading) {
        return (
            <div className="glass-panel p-6 rounded-2xl animate-pulse">
                <div className="h-8 bg-sapphire-700/50 rounded w-1/3 mb-4" />
                <div className="space-y-4">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="h-24 bg-sapphire-700/30 rounded-xl" />
                    ))}
                </div>
            </div>
        );
    }

    if (!data) {
        return (
            <div className="glass-panel p-6 rounded-2xl">
                <p className="text-sapphire-300">No recommendations available</p>
            </div>
        );
    }

    return (
        <div className="glass-panel p-6 rounded-2xl space-y-6">
            {/* Header with Overall Risk */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-sapphire-500/20">
                        <ShieldCheck className="h-5 w-5 text-sapphire-400" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-white">Hedging Recommendations</h3>
                        <p className="text-sm text-sapphire-300">AI-generated actionable insights</p>
                    </div>
                </div>
                <div className={cn(
                    'px-3 py-1.5 rounded-lg border text-sm font-medium',
                    getRiskLevelStyle(data.overall_risk_level)
                )}>
                    {data.overall_risk_level.toUpperCase()} RISK
                </div>
            </div>

            {/* Overall Recommendation */}
            <div className="bg-sapphire-800/30 rounded-xl p-4 border border-sapphire-700/50">
                <p className="text-sapphire-100">{data.overall_recommendation}</p>
                {data.estimated_risk_reduction > 0 && (
                    <p className="text-emerald-400 text-sm mt-2">
                        Estimated risk reduction if followed: {data.estimated_risk_reduction.toFixed(0)}%
                    </p>
                )}
            </div>

            {/* Currency Recommendations */}
            <div className="space-y-3">
                {data.currency_recommendations.map((rec) => {
                    const urgencyStyle = getUrgencyStyle(rec.urgency);
                    const ActionIcon = getActionIcon(rec.action);

                    return (
                        <div
                            key={rec.currency}
                            className={cn(
                                'bg-sapphire-800/20 rounded-xl p-4 border transition-all hover:bg-sapphire-800/30',
                                urgencyStyle.border
                            )}
                        >
                            <div className="flex items-start justify-between gap-4">
                                <div className="flex items-start gap-3">
                                    <div className={cn('p-2 rounded-lg', urgencyStyle.bg)}>
                                        <ActionIcon className={cn('h-4 w-4', urgencyStyle.text)} />
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="font-semibold text-white">{rec.currency}</span>
                                            <span className={cn(
                                                'px-2 py-0.5 rounded text-xs font-medium uppercase',
                                                urgencyStyle.bg, urgencyStyle.text
                                            )}>
                                                {rec.action}
                                            </span>
                                            {rec.urgency !== 'monitor' && (
                                                <span className="flex items-center gap-1 text-xs text-sapphire-300">
                                                    <Clock className="h-3 w-3" />
                                                    {rec.urgency}
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-sm text-sapphire-200">{rec.rationale}</p>

                                        {rec.suggested_coverage > 0 && (
                                            <div className="flex items-center gap-4 mt-3 text-sm">
                                                <span className="text-sapphire-300">
                                                    Suggested coverage: <span className="text-white font-medium">{(rec.suggested_coverage * 100).toFixed(0)}%</span>
                                                </span>
                                                <span className="text-sapphire-300">
                                                    Confidence: <span className="text-white font-medium">{(rec.confidence * 100).toFixed(0)}%</span>
                                                </span>
                                            </div>
                                        )}

                                        {rec.instruments.length > 0 && (
                                            <div className="flex flex-wrap gap-2 mt-2">
                                                {rec.instruments.map((inst, i) => (
                                                    <span
                                                        key={i}
                                                        className="px-2 py-1 bg-sapphire-700/30 rounded text-xs text-sapphire-200"
                                                    >
                                                        {inst}
                                                    </span>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Cross-Currency Opportunities */}
            {data.cross_currency_opportunities.length > 0 && (
                <div className="bg-emerald-500/10 rounded-xl p-4 border border-emerald-500/30">
                    <h4 className="text-sm font-medium text-emerald-400 mb-2">Cross-Currency Opportunities</h4>
                    <ul className="space-y-1">
                        {data.cross_currency_opportunities.map((opp, i) => (
                            <li key={i} className="text-sm text-emerald-200 flex items-start gap-2">
                                <span className="text-emerald-400">•</span>
                                {opp}
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}
