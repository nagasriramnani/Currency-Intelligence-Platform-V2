'use client';

import React from 'react';
import { AlertTriangle, TrendingDown, History } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Scenario {
    name: string;
    description: string;
    impacts: {
        EUR: number;
        GBP: number;
        CAD: number;
    };
}

interface StressScenariosProps {
    scenarios: Scenario[];
    isLoading?: boolean;
}

function getImpactColor(impact: number): string {
    if (impact < -10) return 'text-red-400';
    if (impact < -5) return 'text-orange-400';
    if (impact < 0) return 'text-yellow-400';
    if (impact > 5) return 'text-emerald-400';
    return 'text-sapphire-200';
}

function getImpactBg(impact: number): string {
    if (impact < -10) return 'bg-red-500/10';
    if (impact < -5) return 'bg-orange-500/10';
    if (impact < 0) return 'bg-yellow-500/10';
    if (impact > 5) return 'bg-emerald-500/10';
    return 'bg-sapphire-500/10';
}

export function StressScenariosTable({ scenarios, isLoading }: StressScenariosProps) {
    if (isLoading) {
        return (
            <div className="glass-panel p-6 rounded-2xl animate-pulse">
                <div className="h-8 bg-sapphire-700/50 rounded w-1/3 mb-4" />
                <div className="h-64 bg-sapphire-700/30 rounded-xl" />
            </div>
        );
    }

    return (
        <div className="glass-panel p-6 rounded-2xl space-y-6">
            {/* Header */}
            <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-orange-500/20">
                    <AlertTriangle className="h-5 w-5 text-orange-400" />
                </div>
                <div>
                    <h3 className="text-lg font-semibold text-white">Stress Test Scenarios</h3>
                    <p className="text-sm text-sapphire-300">Historical crisis impact analysis</p>
                </div>
            </div>

            {/* Scenarios Table */}
            <div className="overflow-x-auto">
                <table className="w-full">
                    <thead>
                        <tr className="border-b border-sapphire-700/50">
                            <th className="text-left py-3 px-4 text-sm font-medium text-sapphire-300">Scenario</th>
                            <th className="text-center py-3 px-4 text-sm font-medium text-sapphire-300">EUR</th>
                            <th className="text-center py-3 px-4 text-sm font-medium text-sapphire-300">GBP</th>
                            <th className="text-center py-3 px-4 text-sm font-medium text-sapphire-300">CAD</th>
                        </tr>
                    </thead>
                    <tbody>
                        {scenarios.map((scenario, index) => (
                            <tr
                                key={scenario.name}
                                className={cn(
                                    'border-b border-sapphire-800/50 hover:bg-sapphire-800/20 transition-colors',
                                    index === scenarios.length - 1 && 'border-b-0'
                                )}
                            >
                                <td className="py-4 px-4">
                                    <div className="flex items-start gap-3">
                                        <History className="h-4 w-4 text-sapphire-400 mt-1 flex-shrink-0" />
                                        <div>
                                            <span className="font-medium text-white">{scenario.name}</span>
                                            <p className="text-xs text-sapphire-400 mt-0.5">{scenario.description}</p>
                                        </div>
                                    </div>
                                </td>
                                {(['EUR', 'GBP', 'CAD'] as const).map((currency) => {
                                    const impact = scenario.impacts[currency];
                                    return (
                                        <td key={currency} className="py-4 px-4 text-center">
                                            <span
                                                className={cn(
                                                    'inline-flex items-center gap-1 px-2 py-1 rounded',
                                                    getImpactBg(impact),
                                                    getImpactColor(impact),
                                                    'font-medium text-sm'
                                                )}
                                            >
                                                {impact > 0 ? '+' : ''}{impact.toFixed(1)}%
                                                <TrendingDown
                                                    className={cn(
                                                        'h-3 w-3',
                                                        impact > 0 && 'rotate-180'
                                                    )}
                                                />
                                            </span>
                                        </td>
                                    );
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Legend */}
            <div className="flex flex-wrap gap-4 pt-4 border-t border-sapphire-700/30 text-xs">
                <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded bg-red-500/30" />
                    <span className="text-sapphire-300">Severe (&lt;-10%)</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded bg-orange-500/30" />
                    <span className="text-sapphire-300">High (&lt;-5%)</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded bg-yellow-500/30" />
                    <span className="text-sapphire-300">Moderate (&lt;0%)</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded bg-emerald-500/30" />
                    <span className="text-sapphire-300">Positive (&gt;5%)</span>
                </div>
            </div>

            {/* Note */}
            <div className="bg-sapphire-800/20 rounded-lg p-3 text-xs text-sapphire-300">
                <strong className="text-sapphire-200">Note:</strong> Values show historical percentage moves
                during each crisis. Use these to stress-test current portfolio exposures.
            </div>
        </div>
    );
}
