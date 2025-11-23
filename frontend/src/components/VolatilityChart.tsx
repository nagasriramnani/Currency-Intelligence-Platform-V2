/**
 * Volatility / Regime Chart
 * Visualization #3: Shows rolling volatility over time
 */

import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { formatDateShort, getCurrencyColor } from '@/lib/utils';
import type { TimeSeriesDataPoint } from '@/lib/api';

interface VolatilityChartProps {
  data: TimeSeriesDataPoint[];
}

export function VolatilityChart({ data }: VolatilityChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-96 text-sapphire-400">
        No data available
      </div>
    );
  }

  // Group by date and currency
  const groupedByDate = data.reduce((acc, point) => {
    if (point.rolling_volatility === null) return acc;

    const date = point.record_date;
    if (!acc[date]) {
      acc[date] = { date };
    }
    acc[date][`${point.currency}_vol`] = point.rolling_volatility;
    return acc;
  }, {} as Record<string, any>);

  const chartData = Object.values(groupedByDate).sort(
    (a: any, b: any) => new Date(a.date).getTime() - new Date(b.date).getTime()
  );

  // Calculate mean volatility for reference line
  const allVolatilities = data
    .filter((d) => d.rolling_volatility !== null)
    .map((d) => d.rolling_volatility as number);
  const meanVolatility =
    allVolatilities.reduce((sum, val) => sum + val, 0) / allVolatilities.length;

  const currencies = ['EUR', 'GBP', 'CAD'];

  return (
    <div className="space-y-6 p-4">
      <ResponsiveContainer width="100%" height={350}>
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
          <XAxis
            dataKey="date"
            tickFormatter={(date) => formatDateShort(date)}
            stroke="#94A3B8"
            style={{ fontSize: '12px' }}
            tick={{ fill: '#94A3B8' }}
          />
          <YAxis
            stroke="#94A3B8"
            style={{ fontSize: '12px' }}
            tick={{ fill: '#94A3B8' }}
            label={{
              value: 'Volatility (%)',
              angle: -90,
              position: 'insideLeft',
              style: { fontSize: '12px', fill: '#94A3B8' },
            }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '8px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
              color: '#f8fafc'
            }}
            itemStyle={{ color: '#f8fafc' }}
            labelFormatter={(date) => formatDateShort(date)}
            formatter={(value: number) => [`${value.toFixed(2)}%`, 'Volatility']}
          />
          <Legend wrapperStyle={{ paddingTop: '20px' }} />

          <ReferenceLine
            y={meanVolatility}
            stroke="#FACC15"
            strokeDasharray="5 5"
            label={{
              value: 'Mean',
              position: 'right',
              fill: '#94A3B8',
              fontSize: 12,
            }}
          />

          {currencies.map((currency) => (
            <Line
              key={currency}
              type="monotone"
              dataKey={`${currency}_vol`}
              name={`${currency} Volatility`}
              stroke={getCurrencyColor(currency)}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6, stroke: '#fff', strokeWidth: 2 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>

      <div className="mt-4 p-4 bg-sapphire-900/50 border border-sapphire-800/50 rounded-xl">
        <p className="text-sm text-sapphire-200 leading-relaxed">
          <strong className="text-sapphire-400">Volatility Insight:</strong> Higher values indicate more volatile periods with
          larger price swings. The yellow dashed line shows the historical average volatility.
        </p>
      </div>
    </div>
  );
}


