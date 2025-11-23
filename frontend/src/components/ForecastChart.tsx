/**
 * Forecast vs Actual Chart
 * Visualization #4: Shows ML forecast with confidence intervals
 */

import React, { useMemo } from 'react';
import {
  LineChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts';
import { Sparkles } from 'lucide-react';
import { formatDateShort, getCurrencyColor } from '@/lib/utils';
import type { ForecastData } from '@/lib/api';
import { ForecastScenario, adjustForecastForScenario } from '@/lib/insights';

interface ForecastChartProps {
  forecastData?: ForecastData;
  currency: string;
  scenario: ForecastScenario;
}

export function ForecastChart({ forecastData, currency, scenario }: ForecastChartProps) {
  const adjustedSeries = useMemo(() => adjustForecastForScenario(forecastData, scenario), [forecastData, scenario]);

  const chartData = useMemo(() => {
    if (!forecastData) return [];

    const confidenceMap = new Map(adjustedSeries.confidence.map((band) => [band.date, band]));

    const historical = (forecastData.historical ?? [])
      .map((point) => ({
        date: point.date,
        actual: point.value,
        forecast: null,
        lower: null,
        upper: null,
        type: 'historical' as const,
      }))
      .slice(-36);

    const forecastSeries = adjustedSeries.forecast.map((point) => {
      const band = confidenceMap.get(point.date);
      return {
        date: point.date,
        actual: null,
        forecast: point.value,
        lower: band?.lower ?? null,
        upper: band?.upper ?? null,
        type: 'forecast' as const,
      };
    });

    if (!historical.length) {
      return forecastSeries;
    }

    if (!forecastSeries.length) {
      return historical;
    }

    const bridgePoint = {
      date: forecastSeries[0].date,
      actual: historical[historical.length - 1].actual,
      forecast: forecastSeries[0].forecast,
      lower: forecastSeries[0].lower,
      upper: forecastSeries[0].upper,
      type: 'transition' as const,
    };

    return [...historical, bridgePoint, ...forecastSeries.slice(1)];
  }, [forecastData, adjustedSeries]);

  if (!forecastData || chartData.length === 0) {
    return (
      <div className="flex h-96 items-center justify-center text-sapphire-400">
        No data available
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData} margin={{ top: 10, right: 24, left: 10, bottom: 5 }}>
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
            domain={['auto', 'auto']}
            tick={{ fill: '#94A3B8' }}
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
            formatter={(value: any, name: string) => {
              if (value === null || value === undefined) return null;
              const label = name === 'actual' ? 'Actual' : name === 'forecast' ? 'Forecast' : name;
              return [Number(value).toFixed(4), label];
            }}
          />
          <Legend
            verticalAlign="top"
            align="left"
            wrapperStyle={{ paddingBottom: 20 }}
            payload={[
              { value: 'Actual', type: 'line', color: '#3B82F6', id: 'actual' },
              { value: 'Forecast', type: 'line', color: '#FACC15', id: 'forecast' },
              { value: 'Confidence Band', type: 'rect', color: '#FACC15', id: 'band' },
            ]}
          />

          {forecastData.forecast_start && (
            <ReferenceLine
              x={forecastData.forecast_start}
              stroke="#64748B"
              strokeDasharray="3 3"
              label={{
                position: 'top',
                value: 'Forecast starts',
                fill: '#94A3B8',
                fontSize: 11,
              }}
            />
          )}

          <Area
            type="monotone"
            dataKey="upper"
            stroke="none"
            fill="#FACC15"
            fillOpacity={0.1}
            name="Upper band"
            isAnimationActive={false}
          />
          <Area
            type="monotone"
            dataKey="lower"
            stroke="none"
            fill="#0B1120" // Match background to hide lower part
            fillOpacity={1}
            name="Lower band"
            isAnimationActive={false}
          />

          <Line
            type="monotone"
            dataKey="actual"
            name="Actual Rate"
            stroke="#3B82F6"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 5, fill: '#3B82F6', stroke: '#fff' }}
            connectNulls
          />

          <Line
            type="monotone"
            dataKey="forecast"
            name="Forecast"
            stroke="#FACC15"
            strokeWidth={2}
            strokeDasharray="5 4"
            dot={{ r: 3, fill: '#FACC15' }}
            activeDot={{ r: 5, fill: '#FACC15', stroke: '#fff' }}
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="rounded-xl bg-sapphire-900/50 border border-sapphire-800/50 p-4">
          <h5 className="mb-2 text-xs font-semibold uppercase tracking-wider text-sapphire-400">Forecast Horizon</h5>
          <p className="text-lg font-bold text-white">
            {forecastData.forecast.length || 0} periods
          </p>
          <p className="mt-1 text-xs text-sapphire-300">
            {forecastData.forecast[0]?.date ?? 'n/a'} to{' '}
            {forecastData.forecast[forecastData.forecast.length - 1]?.date ?? 'n/a'}
          </p>
        </div>

        <div className="rounded-xl bg-sapphire-900/50 border border-sapphire-800/50 p-4">
          <h5 className="mb-2 text-xs font-semibold uppercase tracking-wider text-sapphire-400">Direction</h5>
          <p className="text-lg font-bold text-white">
            {(() => {
              const first = adjustedSeries.forecast[0]?.value;
              const last = adjustedSeries.forecast[adjustedSeries.forecast.length - 1]?.value;
              if (first === undefined || last === undefined) return 'Stable →';
              if (last > first * 1.01) return 'Rising ↑';
              if (last < first * 0.99) return 'Declining ↓';
              return 'Stable →';
            })()}
          </p>
          <p className="mt-1 text-xs text-sapphire-300">
            From {adjustedSeries.forecast[0]?.value?.toFixed(4) ?? 'n/a'} to{' '}
            {adjustedSeries.forecast[adjustedSeries.forecast.length - 1]?.value?.toFixed(4) ?? 'n/a'}
          </p>
        </div>

        <div className="rounded-xl bg-sapphire-900/50 border border-sapphire-800/50 p-4">
          <h5 className="mb-2 text-xs font-semibold uppercase tracking-wider text-sapphire-400">Confidence</h5>
          {adjustedSeries.confidence.length > 0 ? (
            <>
              <p className="text-lg font-bold text-white">
                {adjustedSeries.confidence[0].lower.toFixed(4)} -{' '}
                {adjustedSeries.confidence[adjustedSeries.confidence.length - 1].upper.toFixed(4)}
              </p>
              <p className="mt-1 text-xs text-sapphire-300">
                80% interval range
              </p>
            </>
          ) : (
            <p className="text-sm text-sapphire-300">Confidence band not available.</p>
          )}
        </div>
      </div>

      <div className="rounded-lg bg-sapphire-800/30 p-4 border border-sapphire-700/30">
        <p className="text-sm leading-relaxed text-sapphire-200">
          The solid line tracks realised USD/{currency} rates. The yellow dashed line shows the
          scenario-adjusted forward view and the shaded band marks the forecast uncertainty. A steeper
          slope or widening band indicates higher risk ahead.
        </p>
      </div>

      {forecastData.insight && (
        <div className="flex gap-3 rounded-lg border border-sapphire-700/50 bg-sapphire-900/30 p-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-sapphire-500/10 text-sapphire-400 border border-sapphire-500/20">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-sapphire-400">
              AI Forecast Insight
            </p>
            <p className="mt-1 text-sm leading-relaxed text-sapphire-100">
              {forecastData.insight}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

