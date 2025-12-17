'use client';

import React, { useMemo, useState, useEffect } from 'react';
import { useTimeSeriesData } from '@/hooks/useCurrencyData';
import { groupDataByCurrency, alignTimeSeries, calculateCorrelation } from '@/lib/analysis';
import { SkeletonBlock } from '@/components/SkeletonBlock';
import { getCurrencyColor } from '@/lib/utils';

export function CorrelationMatrix() {
    // Track if component has mounted on client to prevent hydration mismatch
    const [hasMounted, setHasMounted] = useState(false);

    useEffect(() => {
        setHasMounted(true);
    }, []);

    // Fetch data for the last 90 days for correlation analysis
    const endDate = new Date().toISOString().split('T')[0];
    const startDate = new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

    const { data: timeSeriesData, isLoading } = useTimeSeriesData(['EUR', 'GBP', 'CAD'], startDate, endDate);

    const correlations = useMemo(() => {
        if (!timeSeriesData?.data) return [];

        const grouped = groupDataByCurrency(timeSeriesData.data);
        const currencies = ['EUR', 'GBP', 'CAD'];
        const matrix: { x: string; y: string; value: number }[] = [];

        currencies.forEach(currX => {
            currencies.forEach(currY => {
                if (currX === currY) {
                    matrix.push({ x: currX, y: currY, value: 1 });
                } else {
                    const dataX = grouped[currX] || [];
                    const dataY = grouped[currY] || [];
                    const { x, y } = alignTimeSeries(dataX, dataY);
                    const corr = calculateCorrelation(x, y);
                    matrix.push({ x: currX, y: currY, value: corr });
                }
            });
        });

        return matrix;
    }, [timeSeriesData]);

    // Show skeleton on server AND during initial client mount to prevent hydration mismatch
    if (!hasMounted || isLoading) {
        return <SkeletonBlock className="h-[300px] w-full" />;
    }

    const currencies = ['EUR', 'GBP', 'CAD'];

    const getColor = (value: number) => {
        if (value === 1) return 'bg-sapphire-800/50 text-white';
        // Map correlation -1 to 1 to a color scale
        // Strong positive: Emerald
        // Strong negative: Rose
        // Neutral: Sapphire
        if (value > 0.5) return `bg-emerald-500/${Math.round(value * 40)} text-emerald-300`;
        if (value < -0.5) return `bg-rose-500/${Math.round(Math.abs(value) * 40)} text-rose-300`;
        return 'bg-sapphire-800/20 text-sapphire-300';
    };

    return (
        <div className="overflow-x-auto">
            <table className="w-full border-collapse">
                <thead>
                    <tr>
                        <th className="p-2"></th>
                        {currencies.map(c => (
                            <th key={c} className="p-2 text-sm font-bold text-white">
                                {c}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {currencies.map(rowCurr => (
                        <tr key={rowCurr}>
                            <td className="p-2 text-sm font-bold text-white text-right">{rowCurr}</td>
                            {currencies.map(colCurr => {
                                const item = correlations.find(c => c.x === rowCurr && c.y === colCurr);
                                const value = item?.value || 0;
                                return (
                                    <td key={colCurr} className="p-1">
                                        <div
                                            className={`h-16 w-full rounded-lg flex items-center justify-center text-sm font-medium transition-all hover:scale-105 ${getColor(value)}`}
                                            title={`Correlation between ${rowCurr} and ${colCurr}: ${value.toFixed(4)}`}
                                        >
                                            {value.toFixed(2)}
                                        </div>
                                    </td>
                                );
                            })}
                        </tr>
                    ))}
                </tbody>
            </table>
            <div className="mt-4 flex justify-center gap-6 text-xs text-sapphire-300">
                <div className="flex items-center gap-2">
                    <div className="h-3 w-3 rounded bg-emerald-500/40"></div>
                    <span>Positive Correlation</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="h-3 w-3 rounded bg-rose-500/40"></div>
                    <span>Negative Correlation</span>
                </div>
            </div>
        </div>
    );
}
