'use client';

import React from 'react';
import { Shield, AlertTriangle, TrendingDown, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';

interface VaRData {
    currency: string;
    confidence: number;
    horizon_days: number;
    var: {
        parametric: number;
        historical: number;
        monte_carlo: number | null;
    };
    cvar: number;
    volatility: number;
    stress_tests: Record<string, number>;
}

interface VaRPanelProps {
    data: Record<string, VaRData>;
    confidence: number;
    horizonDays: number;
    isLoading?: boolean;
}

function getRiskLevel(var_value: number): { level: string; color: string; bg: string } {
    if (var_value > 3.0) {
        return { level: 'Critical', color: 'text-red-400', bg: 'bg-red-500/20' };
    } else if (var_value > 2.0) {
        return { level: 'High', color: 'text-orange-400', bg: 'bg-orange-500/20' };
    } else if (var_value > 1.0) {
        return { level: 'Moderate', color: 'text-yellow-400', bg: 'bg-yellow-500/20' };
    } else {
        return { level: 'Low', color: 'text-emerald-400', bg: 'bg-emerald-500/20' };
    }
}

export function VaRPanel({ data, confidence, horizonDays, isLoading }: VaRPanelProps) {
    if (isLoading) {
        return (
            <div className="glass-panel p-6 rounded-2xl animate-pulse">
                <div className="h-8 bg-sapphire-700/50 rounded w-1/3 mb-4" />
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="h-40 bg-sapphire-700/30 rounded-xl" />
                    ))}
                </div>
            </div>
        );
    }

    const currencies = Object.keys(data);

    return (
        <div className="glass-panel p-6 rounded-2xl space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-sapphire-500/20">
                        <Shield className="h-5 w-5 text-sapphire-400" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-white">Value at Risk Analysis</h3>
                        <p className="text-sm text-sapphire-300">
                            {(confidence * 100).toFixed(0)}% confidence, {horizonDays}-day horizon
                        </p>
                    </div>
                </div>
            </div>

            {/* Currency VaR Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {currencies.map((currency) => {
                    const currencyData = data[currency];
                    const varValue = currencyData.var.parametric;
                    const risk = getRiskLevel(varValue);

                    return (
                        <div
                            key={currency}
                            className="bg-sapphire-800/30 rounded-xl p-4 border border-sapphire-700/50 hover:border-sapphire-600/50 transition-all"
                        >
                            {/* Currency Header */}
                            <div className="flex items-center justify-between mb-4">
                                <span className="text-lg font-bold text-white">USD/{currency}</span>
                                <span className={cn('px-2 py-1 rounded-full text-xs font-medium', risk.bg, risk.color)}>
                                    {risk.level}
                                </span>
                            </div>

                            {/* VaR Metrics */}
                            <div className="space-y-3">
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-sapphire-300">VaR (Parametric)</span>
                                    <span className="text-lg font-semibold text-white">
                                        {varValue.toFixed(2)}%
                                    </span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-sapphire-300">VaR (Historical)</span>
                                    <span className="text-sm text-sapphire-100">
                                        {currencyData.var.historical.toFixed(2)}%
                                    </span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-sapphire-300">CVaR (Expected Shortfall)</span>
                                    <span className="text-sm text-orange-400">
                                        {currencyData.cvar.toFixed(2)}%
                                    </span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-sapphire-300">Volatility (Ann.)</span>
                                    <span className="text-sm text-sapphire-100">
                                        {currencyData.volatility.toFixed(1)}%
                                    </span>
                                </div>
                            </div>

                            {/* Risk Bar */}
                            <div className="mt-4 pt-4 border-t border-sapphire-700/50">
                                <div className="h-2 bg-sapphire-900/50 rounded-full overflow-hidden">
                                    <div
                                        className={cn(
                                            'h-full rounded-full transition-all duration-500',
                                            varValue > 3.0 ? 'bg-red-500' :
                                                varValue > 2.0 ? 'bg-orange-500' :
                                                    varValue > 1.0 ? 'bg-yellow-500' :
                                                        'bg-emerald-500'
                                        )}
                                        style={{ width: `${Math.min(varValue * 25, 100)}%` }}
                                    />
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Explanation */}
            <div className="bg-sapphire-800/20 rounded-lg p-4 border border-sapphire-700/30">
                <div className="flex items-start gap-3">
                    <AlertTriangle className="h-5 w-5 text-yellow-400 mt-0.5 flex-shrink-0" />
                    <div className="text-sm text-sapphire-200">
                        <strong className="text-sapphire-100">How to interpret:</strong> VaR indicates the maximum
                        expected loss at {(confidence * 100).toFixed(0)}% confidence over {horizonDays} day(s).
                        A VaR of 2% means there's a {((1 - confidence) * 100).toFixed(0)}% chance of losing more than 2%.
                        CVaR shows the expected loss when VaR is breached.
                    </div>
                </div>
            </div>
        </div>
    );
}
