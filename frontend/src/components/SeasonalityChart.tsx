'use client';

import React, { useMemo, useState } from 'react';
import { useTimeSeriesData } from '@/hooks/useCurrencyData';
import { calculateSeasonality, groupDataByCurrency } from '@/lib/analysis';
import { SkeletonBlock } from '@/components/SkeletonBlock';
import { getCurrencyColor } from '@/lib/utils';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    Cell
} from 'recharts';

export function SeasonalityChart() {
    const [selectedCurrency, setSelectedCurrency] = useState('EUR');

    // Fetch 5 years of data for seasonality
    const endDate = new Date().toISOString().split('T')[0];
    const startDate = new Date(Date.now() - 5 * 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

    const { data: timeSeriesData, isLoading } = useTimeSeriesData([selectedCurrency], startDate, endDate);

    const seasonalityData = useMemo(() => {
        if (!timeSeriesData?.data) return [];
        return calculateSeasonality(timeSeriesData.data);
    }, [timeSeriesData]);

    if (isLoading) {
        return <SkeletonBlock className="h-[350px] w-full" />;
    }

    return (
        <div className="space-y-4">
            <div className="flex justify-end gap-2">
                {['EUR', 'GBP', 'CAD'].map(curr => (
                    <button
                        key={curr}
                        onClick={() => setSelectedCurrency(curr)}
                        className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${selectedCurrency === curr
                            ? 'bg-sapphire-500 text-white shadow-lg shadow-sapphire-500/25'
                            : 'bg-sapphire-800/30 text-sapphire-300 hover:bg-sapphire-800/50 hover:text-white'
                            }`}
                    >
                        {curr}
                    </button>
                ))}
            </div>

            <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={seasonalityData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                        <XAxis
                            dataKey="month"
                            stroke="#94A3B8"
                            tick={{ fill: '#94A3B8', fontSize: 12 }}
                            axisLine={false}
                            tickLine={false}
                        />
                        <YAxis
                            stroke="#94A3B8"
                            tick={{ fill: '#94A3B8', fontSize: 12 }}
                            axisLine={false}
                            tickLine={false}
                            tickFormatter={(val) => `${val.toFixed(2)}%`}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: '#1e293b',
                                border: '1px solid #334155',
                                borderRadius: '8px',
                                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                                color: '#f8fafc'
                            }}
                            formatter={(val: number) => [`${val.toFixed(3)}%`, 'Avg Return']}
                            cursor={{ fill: '#334155', opacity: 0.4 }}
                        />
                        <Bar dataKey="avgReturn" radius={[4, 4, 0, 0]}>
                            {seasonalityData.map((entry, index) => (
                                <Cell
                                    key={`cell-${index}`}
                                    fill={entry.avgReturn >= 0 ? '#10B981' : '#F43F5E'}
                                    fillOpacity={0.8}
                                />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>

            <p className="text-xs text-center text-sapphire-400">
                Average monthly returns over the last 5 years. Positive bars indicate months of appreciation against USD.
            </p>
        </div>
    );
}
