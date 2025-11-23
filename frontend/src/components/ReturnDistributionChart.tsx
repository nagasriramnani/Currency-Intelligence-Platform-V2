/**
 * Return Distribution & Relative Risk Chart
 * Visualization #5: Shows comparative risk/return profiles
 */

import React, { useMemo } from 'react';
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
} from 'recharts';
import { getCurrencyColor } from '@/lib/utils';
import type { TimeSeriesDataPoint } from '@/lib/api';

interface ReturnDistributionChartProps {
  data: TimeSeriesDataPoint[];
}

export function ReturnDistributionChart({ data }: ReturnDistributionChartProps) {
  const statistics = useMemo(() => {
    if (!data || data.length === 0) return [];

    const currencies = ['EUR', 'GBP', 'CAD'];
    
    return currencies.map((currency) => {
      const currencyData = data
        .filter((d) => d.currency === currency && d.returns !== null)
        .map((d) => d.returns as number)
        .sort((a, b) => a - b);

      if (currencyData.length === 0) {
        return {
          currency,
          mean: 0,
          median: 0,
          std: 0,
          p5: 0,
          p95: 0,
          min: 0,
          max: 0,
        };
      }

      const mean = currencyData.reduce((sum, val) => sum + val, 0) / currencyData.length;
      const median = currencyData[Math.floor(currencyData.length / 2)];
      
      const variance =
        currencyData.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) /
        currencyData.length;
      const std = Math.sqrt(variance);

      const p5Index = Math.floor(currencyData.length * 0.05);
      const p95Index = Math.floor(currencyData.length * 0.95);

      return {
        currency,
        mean,
        median,
        std,
        p5: currencyData[p5Index],
        p95: currencyData[p95Index],
        min: currencyData[0],
        max: currencyData[currencyData.length - 1],
      };
    });
  }, [data]);

  const boxPlotData = useMemo(() => {
    return statistics.map((stat) => ({
      currency: stat.currency,
      min: stat.min,
      q1: stat.p5,
      median: stat.median,
      q3: stat.p95,
      max: stat.max,
      range: stat.p95 - stat.p5,
    }));
  }, [statistics]);

  if (statistics.length === 0) {
    return (
      <div className="flex items-center justify-center h-96 text-sapphire-gray">
        No data available
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Range chart (simplified box plot) */}
      <div>
        <h4 className="text-lg font-semibold text-sapphire-dark mb-4">
          Return Range (5th to 95th Percentile)
        </h4>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart
            data={boxPlotData}
            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            layout="vertical"
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#E8F0FF" />
            <XAxis
              type="number"
              stroke="#616977"
              style={{ fontSize: '12px' }}
              label={{ value: 'Return (%)', position: 'bottom' }}
            />
            <YAxis
              type="category"
              dataKey="currency"
              stroke="#616977"
              style={{ fontSize: '14px', fontWeight: '600' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #E8F0FF',
                borderRadius: '8px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              }}
              formatter={(value: number) => `${value.toFixed(2)}%`}
            />
            <Bar dataKey="range" name="Return Range" radius={[0, 4, 4, 0]}>
              {boxPlotData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getCurrencyColor(entry.currency)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Statistics table */}
      <div>
        <h4 className="text-lg font-semibold text-sapphire-dark mb-4">Statistical Summary</h4>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-sapphire-light">
              <tr>
                <th className="px-4 py-3 text-left font-semibold text-sapphire-dark">
                  Currency
                </th>
                <th className="px-4 py-3 text-right font-semibold text-sapphire-dark">
                  Mean Return
                </th>
                <th className="px-4 py-3 text-right font-semibold text-sapphire-dark">
                  Median
                </th>
                <th className="px-4 py-3 text-right font-semibold text-sapphire-dark">
                  Std Dev
                </th>
                <th className="px-4 py-3 text-right font-semibold text-sapphire-dark">
                  5th %ile
                </th>
                <th className="px-4 py-3 text-right font-semibold text-sapphire-dark">
                  95th %ile
                </th>
              </tr>
            </thead>
            <tbody>
              {statistics.map((stat, idx) => (
                <tr
                  key={stat.currency}
                  className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
                >
                  <td className="px-4 py-3 font-semibold">
                    <span style={{ color: getCurrencyColor(stat.currency) }}>
                      {stat.currency}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span
                      className={
                        stat.mean > 0
                          ? 'text-success'
                          : stat.mean < 0
                          ? 'text-danger'
                          : 'text-sapphire-gray'
                      }
                    >
                      {stat.mean.toFixed(3)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-sapphire-gray">
                    {stat.median.toFixed(3)}%
                  </td>
                  <td className="px-4 py-3 text-right text-sapphire-dark font-medium">
                    {stat.std.toFixed(3)}%
                  </td>
                  <td className="px-4 py-3 text-right text-danger">
                    {stat.p5.toFixed(3)}%
                  </td>
                  <td className="px-4 py-3 text-right text-success">
                    {stat.p95.toFixed(3)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="p-4 bg-sapphire-light rounded-lg">
        <p className="text-sm text-sapphire-dark">
          <strong>Risk Insight:</strong> Standard deviation shows volatility. Higher values
          indicate more variable returns. The 5th and 95th percentiles capture the typical
          range of movements, helping assess downside and upside potential.
        </p>
      </div>
    </div>
  );
}


