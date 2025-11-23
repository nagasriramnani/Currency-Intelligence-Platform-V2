/**
 * Year-on-Year Comparison Chart
 * Visualization #2: Shows YoY performance comparison
 */

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  LabelList,
} from 'recharts';
import { getCurrencyColor, formatPercentage } from '@/lib/utils';
import type { YoYComparison } from '@/lib/api';

interface YoYComparisonChartProps {
  data: YoYComparison[];
}

export function YoYComparisonChart({ data }: YoYComparisonChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-96 text-sapphire-400">
        No data available
      </div>
    );
  }

  const chartData = data.map((item) => ({
    currency: item.currency,
    'Current Rate': item.current_rate,
    'Year Ago Rate': item.year_ago_rate || 0,
    yoyChange: item.yoy_change_pct || 0,
  }));

  const CustomLabel = (props: any) => {
    const { x, y, width, value } = props;
    return (
      <text
        x={x + width / 2}
        y={y - 10}
        fill="#94A3B8"
        textAnchor="middle"
        fontSize={12}
        fontWeight="bold"
      >
        {formatPercentage(value)}
      </text>
    );
  };

  const changePillClasses = (change?: number | null) => {
    const base =
      'mt-2 px-3 py-1 rounded-full text-sm font-semibold transition-colors duration-200 border';

    if (change && change > 0) {
      return `${base} bg-emerald-500/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/20`;
    }

    if (change && change < 0) {
      return `${base} bg-rose-500/10 text-rose-400 border-rose-500/20 hover:bg-rose-500/20`;
    }

    return `${base} bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700`;
  };

  return (
    <div className="space-y-6 p-4">
      <ResponsiveContainer width="100%" height={350}>
        <BarChart data={chartData} margin={{ top: 30, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
          <XAxis
            dataKey="currency"
            stroke="#94A3B8"
            style={{ fontSize: '14px', fontWeight: '600' }}
            tick={{ fill: '#94A3B8' }}
          />
          <YAxis
            stroke="#94A3B8"
            style={{ fontSize: '12px' }}
            tick={{ fill: '#94A3B8' }}
            label={{ value: 'Exchange Rate', angle: -90, position: 'insideLeft', fill: '#94A3B8' }}
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
            formatter={(value: number) => value.toFixed(4)}
            cursor={{ fill: '#334155', opacity: 0.4 }}
          />
          <Legend wrapperStyle={{ paddingTop: '10px' }} />

          <Bar dataKey="Year Ago Rate" fill="#64748B" radius={[4, 4, 0, 0]} />
          <Bar dataKey="Current Rate" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getCurrencyColor(entry.currency)} />
            ))}
            <LabelList content={<CustomLabel />} dataKey="yoyChange" position="top" />
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="grid grid-cols-3 gap-4 mt-6">
        {data.map((item) => (
          <div key={item.currency} className="rounded-xl bg-sapphire-900/50 border border-sapphire-800/50 p-4 text-center hover:bg-sapphire-800/50 transition-colors">
            <h4 className="text-lg font-semibold text-white mb-2">
              {item.currency}
            </h4>
            <div className="space-y-2">
              <div>
                <span className="text-xs text-sapphire-400 uppercase tracking-wider">Current</span>
                <p className="text-xl font-bold" style={{ color: getCurrencyColor(item.currency) }}>
                  {item.current_rate.toFixed(4)}
                </p>
              </div>
              <div>
                <span className="text-xs text-sapphire-400 uppercase tracking-wider">Year Ago</span>
                <p className="text-sm text-sapphire-300">
                  {item.year_ago_rate?.toFixed(4) || 'N/A'}
                </p>
              </div>
              <div className="flex justify-center">
                <div className={changePillClasses(item.yoy_change_pct)}>
                  {item.yoy_change_pct ? formatPercentage(item.yoy_change_pct) : 'N/A'}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

