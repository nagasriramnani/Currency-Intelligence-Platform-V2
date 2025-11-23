/**
 * Multi-Currency Time Series Trend Chart
 * Visualization #1: Shows historical trends for EUR, GBP, CAD
 */

import React, { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { formatDateShort, getCurrencyColor } from '@/lib/utils';
import type { TimeSeriesDataPoint } from '@/lib/api';

interface MultiCurrencyTrendChartProps {
  data: TimeSeriesDataPoint[];
  showMovingAverage?: boolean;
}

export function MultiCurrencyTrendChart({
  data,
  showMovingAverage = false,
}: MultiCurrencyTrendChartProps) {
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return [];

    // Group by date
    const groupedByDate = data.reduce((acc, point) => {
      const date = point.record_date;
      if (!acc[date]) {
        acc[date] = { date };
      }
      acc[date][point.currency] = point.exchange_rate;
      return acc;
    }, {} as Record<string, any>);

    // Convert to array and sort by date
    const result = Object.values(groupedByDate).sort(
      (a: any, b: any) => new Date(a.date).getTime() - new Date(b.date).getTime()
    );

    // Calculate moving averages if requested
    if (showMovingAverage && result.length > 3) {
      const window = 3;
      const currencies = ['EUR', 'GBP', 'CAD'];
      
      currencies.forEach(currency => {
        for (let i = 0; i < result.length; i++) {
          if (i >= window - 1) {
            const sum = result
              .slice(i - window + 1, i + 1)
              .reduce((acc: number, item: any) => acc + (item[currency] || 0), 0);
            result[i][`${currency}_MA`] = sum / window;
          }
        }
      });
    }

    return result;
  }, [data, showMovingAverage]);

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-96 text-sapphire-gray">
        No data available
      </div>
    );
  }

  const currencies = ['EUR', 'GBP', 'CAD'];

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E8F0FF" />
        <XAxis
          dataKey="date"
          tickFormatter={(date) => formatDateShort(date)}
          stroke="#616977"
          style={{ fontSize: '12px' }}
        />
        <YAxis
          stroke="#616977"
          style={{ fontSize: '12px' }}
          domain={['auto', 'auto']}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'white',
            border: '1px solid #E8F0FF',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          }}
          labelFormatter={(date) => formatDateShort(date)}
          formatter={(value: number) => [value.toFixed(4), 'Rate']}
        />
        <Legend
          wrapperStyle={{ paddingTop: '20px' }}
          iconType="line"
        />
        
        {currencies.map((currency) => (
          <Line
            key={currency}
            type="monotone"
            dataKey={currency}
            name={`USD/${currency}`}
            stroke={getCurrencyColor(currency)}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 6 }}
          />
        ))}
        
        {showMovingAverage &&
          currencies.map((currency) => (
            <Line
              key={`${currency}_MA`}
              type="monotone"
              dataKey={`${currency}_MA`}
              name={`${currency} MA(3)`}
              stroke={getCurrencyColor(currency)}
              strokeWidth={1}
              strokeDasharray="5 5"
              dot={false}
              opacity={0.5}
            />
          ))}
      </LineChart>
    </ResponsiveContainer>
  );
}


