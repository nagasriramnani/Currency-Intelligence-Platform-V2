'use client';

import React, { useState, useMemo } from 'react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Cell
} from 'recharts';
import { RefreshCw, Play, AlertTriangle } from 'lucide-react';

interface PortfolioState {
    usd: number;
    eur: number;
    gbp: number;
    cad: number;
}

interface ShockState {
    eur: number; // % change
    gbp: number; // % change
    cad: number; // % change
}

const INITIAL_PORTFOLIO: PortfolioState = {
    usd: 100000,
    eur: 50000,
    gbp: 25000,
    cad: 25000,
};

const SCENARIOS = [
    { label: 'USD Crash', shocks: { eur: 15, gbp: 12, cad: 10 } },
    { label: 'EUR Rally', shocks: { eur: 10, gbp: 2, cad: 1 } },
    { label: 'Brexit 2.0', shocks: { eur: 5, gbp: -15, cad: 2 } },
    { label: 'Oil Spike', shocks: { eur: -2, gbp: -1, cad: 12 } }, // CAD correlates with oil
];

export function ScenarioBuilder() {
    const [portfolio, setPortfolio] = useState<PortfolioState>(INITIAL_PORTFOLIO);
    const [shocks, setShocks] = useState<ShockState>({ eur: 0, gbp: 0, cad: 0 });

    // Mock exchange rates (in a real app, these would come from the API)
    const RATES = {
        EUR: 1.08, // 1 EUR = 1.08 USD
        GBP: 1.25, // 1 GBP = 1.25 USD
        CAD: 0.74, // 1 CAD = 0.74 USD
    };

    const calculateTotalValue = (p: PortfolioState, s: ShockState) => {
        const usdVal = p.usd;
        const eurVal = p.eur * RATES.EUR * (1 + s.eur / 100);
        const gbpVal = p.gbp * RATES.GBP * (1 + s.gbp / 100);
        const cadVal = p.cad * RATES.CAD * (1 + s.cad / 100);
        return usdVal + eurVal + gbpVal + cadVal;
    };

    const currentValue = useMemo(() => calculateTotalValue(portfolio, { eur: 0, gbp: 0, cad: 0 }), [portfolio]);
    const projectedValue = useMemo(() => calculateTotalValue(portfolio, shocks), [portfolio, shocks]);

    const change = projectedValue - currentValue;
    const percentChange = (change / currentValue) * 100;

    const chartData = [
        { name: 'Current', value: currentValue },
        { name: 'Projected', value: projectedValue },
    ];

    const handleApplyScenario = (scenarioShocks: ShockState) => {
        setShocks(scenarioShocks);
    };

    const handleReset = () => {
        setShocks({ eur: 0, gbp: 0, cad: 0 });
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Control Panel */}
            <div className="lg:col-span-1 space-y-6">
                <div className="bg-sapphire-900/40 p-4 rounded-xl border border-sapphire-800/50 backdrop-blur-sm">
                    <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <Play className="h-4 w-4 text-sapphire-400" />
                        Portfolio Composition
                    </h3>
                    <div className="space-y-3">
                        {Object.entries(portfolio).map(([currency, amount]) => (
                            <div key={currency} className="flex items-center justify-between">
                                <label className="text-sm text-sapphire-200 uppercase w-12">{currency}</label>
                                <input
                                    type="number"
                                    value={amount}
                                    onChange={(e) => setPortfolio(prev => ({ ...prev, [currency]: Number(e.target.value) }))}
                                    className="bg-sapphire-950/50 border border-sapphire-700 rounded px-3 py-1 text-right text-white text-sm w-full ml-4 focus:border-sapphire-500 focus:outline-none"
                                />
                            </div>
                        ))}
                    </div>
                </div>

                <div className="bg-sapphire-900/40 p-4 rounded-xl border border-sapphire-800/50 backdrop-blur-sm">
                    <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4 text-sapphire-400" />
                        Market Shocks
                    </h3>
                    <div className="grid grid-cols-2 gap-2 mb-4">
                        {SCENARIOS.map((scenario) => (
                            <button
                                key={scenario.label}
                                onClick={() => handleApplyScenario(scenario.shocks)}
                                className="px-3 py-2 bg-sapphire-800/30 hover:bg-sapphire-700/50 border border-sapphire-700/50 rounded-lg text-xs text-sapphire-200 transition-colors text-left"
                            >
                                {scenario.label}
                            </button>
                        ))}
                    </div>

                    <div className="space-y-4 pt-4 border-t border-sapphire-800/50">
                        {['eur', 'gbp', 'cad'].map((curr) => (
                            <div key={curr}>
                                <div className="flex justify-between text-xs mb-1">
                                    <span className="text-sapphire-300 uppercase">{curr} Shock</span>
                                    <span className={`${shocks[curr as keyof ShockState] > 0 ? 'text-emerald-400' : shocks[curr as keyof ShockState] < 0 ? 'text-rose-400' : 'text-sapphire-400'}`}>
                                        {shocks[curr as keyof ShockState] > 0 ? '+' : ''}{shocks[curr as keyof ShockState]}%
                                    </span>
                                </div>
                                <input
                                    type="range"
                                    min="-30"
                                    max="30"
                                    value={shocks[curr as keyof ShockState]}
                                    onChange={(e) => setShocks(prev => ({ ...prev, [curr]: Number(e.target.value) }))}
                                    className="w-full h-1 bg-sapphire-950 rounded-lg appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-sapphire-400"
                                />
                            </div>
                        ))}
                    </div>

                    <button
                        onClick={handleReset}
                        className="mt-4 w-full flex items-center justify-center gap-2 py-2 bg-sapphire-800/50 hover:bg-sapphire-800 text-sapphire-300 text-sm rounded-lg transition-colors"
                    >
                        <RefreshCw className="h-3 w-3" />
                        Reset Scenarios
                    </button>
                </div>
            </div>

            {/* Visualization */}
            <div className="lg:col-span-2 bg-sapphire-900/20 p-6 rounded-xl border border-sapphire-800/30 backdrop-blur-sm flex flex-col">
                <div className="flex justify-between items-start mb-8">
                    <div>
                        <h3 className="text-xl font-bold text-white">Impact Analysis</h3>
                        <p className="text-sapphire-400 text-sm mt-1">Projected portfolio value based on defined shocks.</p>
                    </div>
                    <div className="text-right">
                        <div className="text-sm text-sapphire-400">Net Impact</div>
                        <div className={`text-2xl font-bold ${change >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {change >= 0 ? '+' : ''}{change.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })}
                        </div>
                        <div className={`text-sm ${change >= 0 ? 'text-emerald-500/70' : 'text-rose-500/70'}`}>
                            {percentChange >= 0 ? '+' : ''}{percentChange.toFixed(2)}%
                        </div>
                    </div>
                </div>

                <div className="flex-1 min-h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                            <XAxis
                                dataKey="name"
                                stroke="#94A3B8"
                                tick={{ fill: '#94A3B8' }}
                                axisLine={false}
                                tickLine={false}
                            />
                            <YAxis
                                stroke="#94A3B8"
                                tick={{ fill: '#94A3B8' }}
                                axisLine={false}
                                tickLine={false}
                                tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`}
                            />
                            <Tooltip
                                cursor={{ fill: '#334155', opacity: 0.2 }}
                                contentStyle={{
                                    backgroundColor: '#0f172a',
                                    border: '1px solid #1e293b',
                                    borderRadius: '8px',
                                    color: '#f8fafc'
                                }}
                                formatter={(val: number) => [val.toLocaleString('en-US', { style: 'currency', currency: 'USD' }), 'Value']}
                            />
                            <Bar dataKey="value" barSize={60} radius={[4, 4, 0, 0]}>
                                {chartData.map((entry, index) => (
                                    <Cell
                                        key={`cell-${index}`}
                                        fill={index === 0 ? '#3B82F6' : entry.value >= currentValue ? '#10B981' : '#F43F5E'}
                                    />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
}
